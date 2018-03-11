# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 14:29:34 2018

@author: Xiuyan
"""

from mido import Message, MidiFile, MidiTrack, MetaMessage

#SONG_PATH = "../musicbank"
SONG_PATH = ""

class Song(object):
    """
    Metadata and file pointers etc for song
    """
    def __init__(self, name, file):
        self.name = name
        self.file = SONG_PATH + file
        self.wav = SONG_PATH + self.file.split('.')[0] + ".wav"
        self.melodyfile = self.file.split('.')[0] + "_stripped.mid"
        self.pitch_diff = None
        
        mid = MidiFile(self.melodyfile)
        track = mid.tracks[0]
        for msg in track:
            if msg.type == 'note_on':
                self.firstnote = msg.note
                break
        
    def setFile(self, file):
        self.file = SONG_PATH + file
    
    def fetchUDS():
        return
    
    def fetchMelodyPitchDiff(self):
        """
        Outputs list of intervals' semitone difference
        """
        file = open(self.name + "_stripped.txt", 'r')
        pitch_diff_string = file.readline()
        pitch_diff = pitch_diff_string.split(",")
        file.close()
        self.pitch_diff = pitch_diff
        
    def getMIDI(self):
        return self.file
    
    def getWav(self):
        return self.wav
        
    def getMelodyFile(self):
        return self.melodyfile
    

class SongDatabase(object):
    """
    
    Attributes:
        songs:
    """
    def __init__(self, allSongNames):
        
        self.songs = {}
        for songname in allSongNames:
            self.songs[songname] = Song(songname, songname + ".mid")
    
    def preprocessMelodies(self):
        
        for songname in self.songs.keys():
            self.songs[songname].fetchMelodyPitchDiff()
    
    def getMelody(self, songname):
        
        return self.songs[songname].pitch_diff
    
    def getFirstNote(self, songname):
        return self.songs[songname].firstnote
    
if __name__ == "__main__":
    
    allSongNames = ["twinkle","london_bridge","lullaby","mary_had_a_little_lamb","three_blind_mice"]
    
    songdb = SongDatabase(allSongNames)
    songdb.preprocessMelodies()
    
    melody = songdb.getMelody("twinkle")