# -*- coding: utf-8 -*-
"""
Created on Sat Mar 10 23:58:00 2018

@author: Xiuyan
"""

from mido import Message, MidiFile, MidiTrack, MetaMessage


def print_all_messages(mid):
    # my code here
    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            print(msg)
    
def create_timestamps_string(mid):
    curr = 0
    timestamps = [0]
    track = mid.tracks[0]
    for msg in track:
        
        if msg.type == 'note_on':
            curr += tick2second(msg.time, mid.ticks_per_beat)
        elif msg.type == 'note_off':
            curr += tick2second(msg.time, mid.ticks_per_beat)
            timestamps.append(curr)

    return timestamps
    #ticks2second()
    
def tick2second(time_in_ticks, ticks_per_beat):
    tempo = 500000
    seconds_per_beat = tempo / 1000000.0
    seconds_per_tick = seconds_per_beat / float(ticks_per_beat)
    time_in_seconds = time_in_ticks * seconds_per_tick   
    return time_in_seconds
    
def count_notes(mid):
    count = 0
    track = mid.tracks[0]
    for msg in track:        
        if msg.type == 'note_on':
            count +=1
    return count

def convert_to_length(timestamps, length, reflength):
    converted = []
    for time in timestamps:
        converted.append(time*length/reflength)
    return converted

if __name__ == "__main__":
    
    name = "./musicbank/twinkle"
    melodyname = name + "_stripped"
    mid = MidiFile(melodyname + ".mid")
    count = count_notes(mid)
    timestamps = create_timestamps_string(mid)
    
    orig = MidiFile(name + ".mid")
    converted = convert_to_length(timestamps, orig.length, mid.length)
    