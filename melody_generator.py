# Based on audio_to_midi_melodia github repo by Justin Salamon <justin.salamon@nyu.edu>
import time
import argparse
import os
import numpy as np
from scipy.signal import medfilt
import __init__
import pyaudio
import sys
import aubio
from aubio import sink
from songmatch import SongMatch
from operator import itemgetter

def get_seq(pitch_seq):
    seq = ["_"]
    for i,p in enumerate(pitch_seq[1:]):
        prev_p = pitch_seq[i]
        if p - prev_p > 0.5:
            seq.append("U")
        elif abs(p - prev_p) <= 0.5:
            seq.append("S")
        else:
            seq.append("D")
    return seq


def midi_to_notes(midi):
    pitches = [[]]
    start = True
    for n, p in enumerate(midi):
        pitch = p
        if (pitch < 1 or pitch > 100) and not start:
            start = True
            pitches.append([])
        if pitch > 1 and pitch < 100:
            start = False
            # if beginning of speaking 
            if len(pitches[-1]) < 2 and abs(pitch - np.mean(pitches[-1])) > 1.5:
                pitches[-1] = [pitch]
            # if not beginning of speaking
            else:
                if abs(pitch - np.mean(pitches[-1])) > 1.5:
                    pitches.append([pitch])
                else:
                    pitches[-1].append(pitch)
                     
    pitch_means = []
    for p in pitches:
        if len(p) > 5:
            pitch_means.append(np.mean(p))
    

    return pitch_means


# pyaudio params
buffer_size = 1024
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100

# setup aubio
tolerance = 0.2
win_s = 4096 # fft size
hop_s = buffer_size # hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)

# setup aubio recording (for debugging)
g = sink('test_record.wav', samplerate=samplerate)

# pitch detection parameters
thresh_high = 100
thresh_low = 1
start_len = 2
pitch_diff_thresh = 1.5
note_min_len = 5
pitches = [[]]
seq = []
start = True

# initialise pyaudio
p = pyaudio.PyAudio()

def append_new(l, n, note_min_len=5):
    if len(l[-1]) <= note_min_len:
        l.pop()
    else:
        l[-1] = np.mean(l[-1])
    l.append(n)
    return l

times = []

def process_audio(in_data, frame_count, time_info, status):
    s = time.time()
    global start
    global pitches
    global seq
    
    signal = np.fromstring(in_data, dtype=np.float32)
    pitch = pitch_o(signal)[0]
    confidence = pitch_o.get_confidence()
    
    # process pitch information
    if (pitch < thresh_low or pitch > thresh_high) and not start:
        start = True
        pitches = append_new(pitches, [])
    if pitch > thresh_low and pitch < thresh_high:
        start = False
        if len(pitches[-1]) < start_len and abs(pitch - pitches[-1]) > pitch_diff_thresh:
                pitches[-1] = [pitch]
        else:
            if abs(pitch - np.mean(pitches[-1])) > pitch_diff_thresh:
                pitches = append_new(pitches, [pitch])
            else:
                pitches[-1].append(pitch)
    
    # if note ends
    if len(pitches) > 2 :
        if (pitches[-2] - pitches[-3]) > 1.0:
            seq.append("U")
        elif abs(pitches[-2] - pitches[-3]) <= 1.0:
            seq.append("S")
        else:
            seq.append("D")
        pitches.pop(0)
    
    g(signal, hop_s)
    times.append(time.time()-s)
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

print(seq)


songs = {'Twinkle Twinkle Little Star':'SUSUSDDSDSDSSSDUSDSDSDUSDSDSDDSUSUSDDSDSDSD',
         'Three Blind Mice':'DDUDDUDSDUDSDUUSDDUUDSSUSSDDUUDSSUSSDDUUDSSDDDDUDDUDDUDSDUDSDUUSDDUUDSSUSSDDUUDSSUSSDDUUDSSDDDD',
         'london Bridge is Falling Down':'UDDDUUDUUDUUSUDDDUUDUDDUUDDDUUDUUDUUSUDDDUUDUDD',
         'Lullaby':'SUDSUDUUDDSDDUUDUUDUUDDUUDSUDDUDDUUUDDSUDDUDDUDDSD',
         'Mary has a little lamb':'DDUUSSDSSUSSDDDUUSSDSUDDUDDUUSSDSSUSSDDDUUSSDSUDD'}

target = "".join(seq[1:])

scores = []
for song in songs:
    song_matcher = SongMatch(songs[song])
    score = song_matcher.addNotes(target)
    scores.append([song,score])
print("+++++++++++++++++++++++++++++++")
print(sorted(scores, key=itemgetter(1))[0][0])
print("+++++++++++++++++++++++++++++++")