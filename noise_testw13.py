# Based on audio_to_midi_melodia github repo by Justin Salamon <justin.salamon@nyu.edu>
import time
import argparse
import os
import numpy as np
from scipy.signal import medfilt
#import __init__
import pyaudio
import sys
import aubio
from aubio import sink
from songmatch import *
from song import *
from operator import itemgetter
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4)
from wavplayer import *
from scipy.io.wavfile import read
import wave

def convert_durations(ds):
    start_time = ds[0][0]
    durations = []
    for i,d in enumerate(ds):
        if i+1 < len(ds):
            durations.append(d[1]-start_time)
    return durations


# pyaudio params
buffer_size = 1024
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
playrate = 44100
seconds_per_sample = buffer_size / samplerate

# setup aubio
tolerance = 0.2
win_s = 4096 # fft size
hop_s = buffer_size # hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)

# setup aubio recording (for debugging)
record_output_fn = 'test.wav'
g = sink(record_output_fn, samplerate=samplerate)
recorded_output = []

# pitch detection parameters
thresh_high = 100
thresh_low = 1
start_len = 2
pitch_diff_thresh = 1.5
note_min_len = 5
pitches = [[]]
durations = [[]] # durations = [[t_start, t_end]...]
seq = []
start = True
UDS = False
start_note = None
time_counter = 0 # time recorded so far (in seconds)
keydiff = None
temporatio = None
startpt = None
matched_song = ""

# song database
allSongNames = ["twinkle","london_bridge","three_blind_mice","boat","lullaby","mary_had_a_little_lamb"]
songdb = SongDatabase(allSongNames)
songdb.preprocessMelodies()
songs = songdb.getAllMelody()
start_notes = songdb.getAllFirstNode()
timestamps = songdb.getAllTimestamps()

# song matcher
song_matcher = SongsMatchNew(songs, timestamps)

def append_new(l, n, d, tc, note_min_len=5):
    if len(l[-1]) <= note_min_len:
        l.pop()
        d.pop()
    else:
        l[-1] = np.mean(l[-1])
        d[-1].append(tc)
    l.append(n)
    d.append([tc])
    return l, d

def reset():
    global pitches
    global durations
    global seq
    global start
    global start_note
    global time_counter
    global song_matcher
    global keydiff
    global temporatio
    global startpt
    global matched_song
    
    pitches = [[]]
    durations = [[]]
    seq = []
    start = True
    start_note = None
    time_counter = 0
    song_matcher = SongsMatchNew(songs, timestamps)
    if detected:
        keydiff = None
        temporatio = None
        startpt = None
        matched_song = ""


def process_audio(signal):
    global start
    global pitches
    global seq
    global start_note
    global time_counter
    global durations
    global keydiff
    global temporatio
    global startpt
    global wf
    global matched_song
    global proc
    global song_matcher
    global recorded_output

    time_counter += seconds_per_sample
    
    pitch = pitch_o(signal)[0]
    confidence = pitch_o.get_confidence()

    # process pitch information
    if (pitch < thresh_low or pitch > thresh_high) and not start:
        start = True
        pitches, durations = append_new(pitches, [], durations, time_counter)
    if pitch > thresh_low and pitch < thresh_high:
        start = False
        if len(pitches[-1]) < start_len and abs(pitch - pitches[-1]) > pitch_diff_thresh:
                pitches[-1] = [pitch]
                durations[-1] = [time_counter] # reset note-start time
        else:
            if abs(pitch - np.mean(pitches[-1])) > pitch_diff_thresh:
                pitches, durations = append_new(pitches, [pitch], durations, time_counter)
            else:
                pitches[-1].append(pitch)
                if not durations[-1]: # if start note
                    durations[-1] = [time_counter]

    # if note ends
    if len(pitches) > 2 :
        if not seq: # if seq empty
            start_note = pitches[-3]
        if UDS:
            if (pitches[-2] - pitches[-3]) > 1.0:
                seq.append("U")
            elif abs(pitches[-2] - pitches[-3]) <= 1.0:
                seq.append("S")
            else:
                seq.append("D")
        else:
            seq.append(int(pitches[-2]-pitches[-3]))
        pitches.pop(0)

        # add the obtained note to song_matcher to get probability
        song_matcher.addNote([seq[-1]])
        scores = song_matcher.getProbDic()
        best_song = sorted(scores.items(), key=itemgetter(1))[-1][0]
        #pp.pprint(scores)
        if max(scores.values()) > 0.8 and best_song != "Others": # if confident enought about song
            matched_song = best_song
            converted_durations = convert_durations(durations)
            keydiff, temporatio, startpt = song_matcher.getKeyTempo(matched_song, start_notes[matched_song], start_note, converted_durations)
#            print("+++++++++++++")
#            print("key difference: %f" %keydiff)
#            print("tempo ratio: %f" %temporatio)
#            print("start point: %f" %startpt)
#            print("song: %s" %matched_song)
#            print("+++++++++++++")
            return True
    return False


recordings_dir = "../test_recording/"
song_names = ["twinkle", "london", "mice", "row", "lullaby", "mary"]
names = ["dami", "matt", "joel", "xiuyan"]
corresp_songs = {"twinkle": "twinkle", "london": "london_bridge", "mice": "three_blind_mice", "row": "boat", "lullaby": "lullaby", "mary": "mary_had_a_little_lamb"}
scores = {}

np.random.seed(0)

for i in range(6): # intensity of noise
    noise_input1 = recordings_dir + "noise_cr.wav"
    noise1_wf = read(noise_input1)[1]
    
    noise_input2 = recordings_dir + "noise_close_cr.wav"
    noise2_wf = read(noise_input2)[1]
    
    noise_wfs = [noise1_wf, noise2_wf]
    for j in range(2): # 2 types of noise
        # first element: 1/0 for accuracy; second element: # of notes for accuracy
        scores_key = "%d-%s"%(i,"ambient" if j == 0 else "close")
        scores[scores_key] = [[],[]]
        
        for k in range(10): # phase-shift of noise
            # prep the noise with random phase shift and intensity 
            noise_wf = noise_wfs[j]
            idx = np.random.randint(len(noise_wf))
            noise = np.hstack((noise_wf[idx:], noise_wf[:idx]))
            for x in range(1): # make noise long enough
                np.append(noise, np.hstack((noise_wf[idx:], noise_wf[:idx])))
            noise *= i
                    
            for l in range(6): # 6 songs in total
                if l < 3: 
                    singer = names[:2]
                else:
                    singer = names[2:]
                curr_song = song_names[l]
                name1 = "%s_%s_quiet.wav" %(curr_song,singer[0])
                name2 = "%s_%s_quiet.wav" %(curr_song,singer[1])
                fnames = [name1, name2]
                
                for m in range(2): # 2 singers each #                    
                    print(fnames[m])
                    vocal_input = recordings_dir + fnames[m]
                    vocal_wf = read(vocal_input)[1]
                    detected = False
                    
                    noise_wf = noise
                    
                    while len(vocal_wf) >= buffer_size and not detected:
                        signal = np.array(vocal_wf[:buffer_size]+noise_wf[:buffer_size], dtype=np.float32)
                        vocal_wf = vocal_wf[buffer_size:]
                        noise_wf = noise_wf[buffer_size:]
                        detected = process_audio(signal)
                    
                    song_title = corresp_songs[curr_song]
                    if detected and matched_song == song_title:
                        print("++++++++++++++ matched! ++++++++++++")
                        scores[scores_key][0].append(1)
                        num_notes = songdb.getNumNotesBefore(song_title, startpt)
                        scores[scores_key][1].append(num_notes)
                    else:
                        scores[scores_key][0].append(0)
                    
                    reset()
                    
#print(scores) 
for score in scores:
    scores[score][0] = np.mean(scores[score][0])
    scores[score][1] = np.mean(scores[score][1])
print(scores)    
                        
                        
                        





