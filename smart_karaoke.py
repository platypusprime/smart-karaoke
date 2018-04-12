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
from wavplayer import WavPlayer
from scipy.io.wavfile import read
import wave

def convert_durations(ds):
    start_time = ds[0][0]
    durations = []
    for i,d in enumerate(ds):
        if i+1 < len(ds):
            durations.append(d[1]-start_time)
    return durations

# if vocal input, set wf = None
song_input = '../test_recording/mary_xiuyan_quiet.wav'
wf = None#read(song_input)[1]
wf_streamout = wave.open(song_input, 'rb')

# pyaudio params
buffer_size = 512
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
detected = False
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

# load all songs
allWavs = {}
for song in allSongNames:
    allWavs[song] = songdb.getWAV(song)
player = WavPlayer(**allWavs)
    
input("Press Enter to continue...")

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
    global detected
    global matched_song
    global player
    global song_matcher
    global recorded_output

    time_counter += seconds_per_sample
    if wf is not None:
        signal = np.array(wf[:frame_count], dtype=np.float32)
        if len(signal) < frame_count:
            if detected:
                player.stop()
            return (in_data, pyaudio.paComplete)
        wf = wf[frame_count:]
        in_data = wf_streamout.readframes(frame_count)
    else:
        signal = np.frombuffer(in_data, dtype=np.float32)
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

    # check if user stopped
    if len(durations) > 1:
        if (time_counter - durations[-1][0]) > 3.0:
            print("######### restarting #########")
            # reset all data
            pitches = [[]]
            durations = [[]]
            seq = []
            start = True
            start_note = None
            time_counter = 0
            song_matcher = SongsMatchNew(songs, timestamps)
            if detected:
                player.stop()
                keydiff = None
                temporatio = None
                startpt = None
                detected = False
                matched_song = ""

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
        if max(scores.values()) > 0.8 and best_song != "Others" and not detected: # if confident enought about song
            matched_song = best_song
            converted_durations = convert_durations(durations)
            keydiff, temporatio, startpt = song_matcher.getKeyTempo(matched_song, start_notes[matched_song], start_note, converted_durations)
            player.curr_file = matched_song
            print(round(startpt*playrate))
            player.navigate(round(startpt*playrate))
            player.time_stretch = temporatio #/ (2**(keydiff/4/12))
            #player.pitch_shift = keydiff/4
            player.play()
            print("+++++++++++++")
            print("key difference: %f" %keydiff)
            print("tempo ratio: %f" %temporatio)
            print("start point: %f" %startpt)
            print("song: %s" %matched_song)
            print("+++++++++++++")
            detected = True
        if detected:
            converted_durations = convert_durations(durations)
            keydiff, temporatio, startpt = song_matcher.getKeyTempo(matched_song, start_notes[matched_song], start_note, converted_durations)
            player.curr_file = matched_song

    g(signal, len(signal))
    return (in_data, pyaudio.paContinue)

# open stream
if wf is None:
    stream = p.open(format=pyaudio_format,
                    channels=n_channels,
                    rate=samplerate,
                    input=True,
                    frames_per_buffer=buffer_size,
                    stream_callback=process_audio)
else:
    stream = p.open(format=p.get_format_from_width(wf_streamout.getsampwidth()),
                    channels=wf_streamout.getnchannels(),
                    rate=wf_streamout.getframerate(),
                    output=True,
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

song_matcher = SongsMatchNew(songs)
song_matcher.addNotes(seq)
scores = song_matcher.getProbDic()
print("+++++++++++++++++++++++++++++++")
print(sorted(scores.items(), key=itemgetter(1))[-1][0])
print("+++++++++++++++++++++++++++++++")
