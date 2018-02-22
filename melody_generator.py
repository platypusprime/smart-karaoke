# Based on audio_to_midi_melodia github repo by Justin Salamon <justin.salamon@nyu.edu>

import librosa
import vamp
import argparse
import os
import numpy as np
from midiutil.MidiFile3 import MIDIFile
from scipy.signal import medfilt
import jams
import __init__
import pyaudio
import sys
import aubio

'''
Extract the melody from an audio file and convert it to MIDI.

The script extracts the melody from an audio file using the Melodia algorithm,
and then segments the continuous pitch sequence into a series of quantized
notes, and exports to MIDI using the provided BPM. If the --jams option is
specified the script will also save the output as a JAMS file. Note that the
JAMS file uses the original note onset/offset times estimated by the algorithm
and ignores the provided BPM value.

Note: Melodia can work pretty well and is the result of several years of
research. The note segmentation/quantization code was hacked in about 30
minutes. Proceed at your own risk... :)

usage: audio_to_midi_melodia.py [-h] [--smooth SMOOTH]
                                [--minduration MINDURATION] [--jams]
                                infile outfile bpm


Examples:
python audio_to_midi_melodia.py --smooth 0.25 --minduration 0.1 --jams
                                ~/song.wav ~/song.mid 60
'''

def save_midi(outfile, notes, tempo):

    track = 0
    time = 0
    midifile = MIDIFile(1)

    # Add track name and tempo.
    midifile.addTrackName(track, time, "MIDI TRACK")
    midifile.addTempo(track, time, tempo)

    channel = 0
    volume = 100

    for note in notes:
        onset = note[0] * (tempo/60.)
        duration = note[1] * (tempo/60.)
        # duration = 1
        pitch = note[2]
        midifile.addNote(track, channel, pitch, onset, duration, volume)

    # And write it to disk.
    binfile = open(outfile, 'wb')
    midifile.writeFile(binfile)
    binfile.close()
    

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


def midi_to_notes(midi, fs, hop, smooth, minduration):

    # smooth midi pitch sequence first
#    if (smooth > 0):
#        filter_duration = smooth  # in seconds
#        filter_size = int(filter_duration * fs / float(hop))
#        if filter_size % 2 == 0:
#            filter_size += 1
#        midi_filt = medfilt(midi, filter_size)
#    else:
#        midi_filt = midi
    # print(len(midi),len(midi_filt))

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
                    
    print(pitches)
    
    
    
    pitch_means = []
    for p in pitches:
        if len(p) > 5:
            pitch_means.append(np.mean(p))
            
    print(pitch_means)
    
#    if len(pitch_means) > 1:
#            
#        corrected_pitches = []
#        for i,p in enumerate(pitch_means):
#            diff = abs(p - np.mean(pitch_means[:i] + pitch_means[i+1:]))
#            if diff < 3:
#                corrected_pitches.append(p)
#    else:
#        corrected_pitches = pitch_means
    
    corrected_pitches = pitch_means

    return corrected_pitches


def hz2midi(hz):

    # convert from Hz to midi note
    hz_nonneg = hz.copy()
    hz_nonneg[hz <= 0] = 0
    midi = 69 + 12*np.log2(hz_nonneg/440.)
    midi[midi <= 0] = 0

    # round
    midi = np.round(midi)

    return midi


def audio_to_midi_melodia(data, outfile, bpm, smooth=0.25, minduration=0.1,
                          savejams=False):

    # define analysis parameters
    fs = 44100
    hop = 128

    # load audio using librosa
#    print("Loading audio...")
#    data, sr = librosa.load(infile, sr=fs, mono=True)
#    data = infile

    # extract melody using melodia vamp plugin
    print("Extracting melody f0 with MELODIA...")
    params = {"minfqr": 100.0, "maxfqr": 800.0, "voicing": 0.9, "minpeaksalience": 0.0}
    melody = vamp.collect(data, sr, "mtg-melodia:melodia",
                          parameters=params)

    # hop = melody['vector'][0]
    pitch = melody['vector'][1]

    # impute missing 0's to compensate for starting timestamp
    pitch = np.insert(pitch, 0, [0]*8)


    # convert f0 to midi notes
    print("Converting Hz to MIDI notes...")
    midi_pitch = hz2midi(pitch)
    print(len(midi_pitch))

    # segment sequence into individual midi notes
    notes, seq = midi_to_notes(midi_pitch, fs, hop, smooth, minduration)
    
    print(notes)
    print(seq)

#    # save note sequence to a midi file
#    print("Saving MIDI to disk...")
#    save_midi(outfile, notes, bpm)

    print("Conversion complete.")

infile = "/home/damichoi/EngSci/Capstone/sample_dami_ds.wav"
outfile= "/home/damichoi/EngSci/Capstone/sample_dami_out.mid"
bpm = 60
smooth = 0.5
minduration = 0.001
jams = False
fs = 44100
hop = 128

# load audio using librosa
print("Loading audio...")
data, sr = librosa.load(infile, sr=fs, mono=True)

print(data.shape)

#audio_to_midi_melodia(data, outfile, bpm, smooth=smooth, minduration=minduration, savejams=jams)



# initialise pyaudio
p = pyaudio.PyAudio()

# open stream
buffer_size = 1024
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                frames_per_buffer=buffer_size)

# setup pitch
tolerance = 0.8
win_s = 4096 # fft size
hop_s = buffer_size # hop size
pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)

pitches = []

print("*** starting recording")
while True:
    try:
        audiobuffer = stream.read(buffer_size)
        signal = np.fromstring(audiobuffer, dtype=np.float32)
    
        pitch = pitch_o(signal)[0]
        confidence = pitch_o.get_confidence()
        pitches.append(pitch)

        print("{} / {}".format(pitch,confidence))

    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()

pitches = midi_to_notes(pitches, fs, hop, smooth, minduration)
print(pitches)
seq = get_seq(pitches)
print(seq)
    
    
