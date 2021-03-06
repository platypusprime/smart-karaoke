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
#from wavplayer import *
from scipy.io.wavfile import read

def convert_durations(ds):
    start_time = ds[0][0]
    durations = []
    for i,d in enumerate(ds):
        if i+1 < len(ds):
            durations.append(d[1]-start_time)
    return durations

# pyaudio params
wf = read('twinkle.wav')[1]
buffer_size = 1024
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
seconds_per_sample = buffer_size / samplerate

# setup aubio
tolerance = 0.2
win_s = 4096 # fft size
hop_s = buffer_size # hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)

# setup aubio recording (for debugging)
record_output_fn = 'record_output.wav'
g = sink(record_output_fn, samplerate=samplerate)

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

# song-matcher setup
# songs = {'Twinkle Twinkle Little Star':[0,7,0,2,0,-2,-2,0,-1,0,-2,0,0,0,-2,7,0,-2,0,-1,0,-2,5,0,-2,0,-1,0,-2,-2,0,7,0,2,0,-2,-2,0,-1,0,-2,0,-2],
#          'Three Blind Mice':[-2,-2,4,-2,-2,7,-2,0,-1,3,-2,0,-1,3,5,0,-1,-2,2,1,-5,0,0,5,0,0,-1,-2,2,1,-5,0,0,5,0,0,-1,-2,2,1,-5,0,0,-2,-1,-2,-2,4,-2,-2,4,-2,-2,7,-2,0,-1,3,-2,0,-1,3,5,0,-1,-2,2,1,-5,0,0,5,0,0,-1,-2,2,1,-5,0,0,5,0,0,-1,-2,2,1,-5,0,0,-2,-1,-2,-2]}
# timestamps = {'Twinkle Twinkle Little Star':[0.49991319444444443, 1.0040273401027078, 1.508141485760971, 2.0122556314192344, 2.516369777077498, 3.020483922735761, 4.0287122140522875, 4.532826359710551, 5.036940505368814, 5.541054651027078, 6.04516879668534, 6.297225869514473, 6.549282942343604, 6.801340015172736, 7.0533970880018675, 7.8641806722689065, 8.565739524976657, 9.06985367063492, 9.573967816293184, 10.078081961951447, 10.582196107609711, 11.086310253267973, 12.0945385445845, 12.598652690242764, 13.102766835901026, 13.606880981559291, 14.110995127217553, 14.615109272875818, 15.11922341853408, 16.127451709850607, 16.63156585550887, 17.135680001167135, 17.6397941468254, 18.14390829248366, 18.648022438141922, 19.152136583800186, 20.160364875116713, 20.664479020774976, 21.16859316643324, 21.672707312091504, 22.176821457749767, 22.68093560340803, 23.18504974906629, 23.995833333333337]}
# start_notes = {'Twinkle Twinkle Little Star': 65}
# wav_files = {'Twinkle Twinkle Little Star':'./musicbank/twinkle.wav',
#              'Three Blind Mice': './musicbank/three_blind_mice.wav'}

# song database
allSongNames = ["twinkle","london_bridge","three_blind_mice","boat","lullaby","mary_had_a_little_lamb"]
songdb = SongDatabase(allSongNames)
songdb.preprocessMelodies()

songs = songdb.getAllMelody()
start_notes = songdb.getAllFirstNode()
timestamps = songdb.getAllTimestamps()

# song matcher
song_matcher = SongsMatchNew(songs, timestamps)

# initialise pyaudio
p = pyaudio.PyAudio()

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


def process_audio(in_data, frame_count, time_info, status):
    ''' callback function for pyaudio'''
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
    
    time_counter += seconds_per_sample
    if wf is not None:
        signal = np.array(wf[:frame_count], dtype=np.float32)
        if len(signal) < frame_count:
            return (in_data, pyaudio.paComplete)
        wf = wf[frame_count:]
    else:
        signal = np.fromstring(in_data, dtype=np.float32)
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
        #pp.pprint(scores)
        if max(scores.values()) > 0.8: # if confident enought about song
            song = sorted(scores.items(), key=itemgetter(1))[-1][0]
            converted_durations = convert_durations(durations)
            keydiff, temporatio, startpt = song_matcher.getKeyTempo(song, start_notes[song], start_note, converted_durations)
            print("+++++++++++++")
            print("key difference: %f" %keydiff)
            print("tempo ration: %f" %temporatio)
            print("start point: %f" %startpt)
            print("song: %s" %song)
            print("+++++++++++++")
#            WavPlayer(wav_files[song])
#            return (in_data, pyaudio.paComplete)


    g(signal, hop_s)
    return (in_data, pyaudio.paContinue)

# open stream
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=buffer_size,
                stream_callback=process_audio)

print("*** starting recording")
stream.start_stream()
while stream.is_active():
    try:
        time.sleep(0.1)
    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()
print(start_note)
print(durations)
print(seq)

print(keydiff, temporatio, startpt)


#         'london Bridge is Falling Down':'UDDDUUDUUDUUSUDDDUUDUDDUUDDDUUDUUDUUSUDDDUUDUDD',
#         'Lullaby':'SUDSUDUUDDSDDUUDUUDUUDDUUDSUDDUDDUUUDDSUDDUDDUDDSD',
#         'Mary has a little lamb':'DDUUSSDSSUSSDDDUUSSDSUDDUDDUUSSDSSUSSDDDUUSSDSUDD'}

song_matcher = SongsMatchNew(songs)
song_matcher.addNotes(seq)
scores = song_matcher.getProbDic()
print("+++++++++++++++++++++++++++++++")
print(sorted(scores.items(), key=itemgetter(1))[-1][0])
print("+++++++++++++++++++++++++++++++")
