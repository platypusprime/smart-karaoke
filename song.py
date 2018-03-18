# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 14:29:34 2018

@author: Xiuyan
"""

from mido import Message, MidiFile, MidiTrack, MetaMessage

SONG_PATH = "musicbank/"

class Song(object):
    """
    Metadata and file pointers etc for song
    """
    def __init__(self, name, file):
        self.name = name
        self.file = SONG_PATH + file
        self.wav = self.file.split('.')[0] + ".wav"
        self.melodyfile = self.file.split('.')[0] + "_stripped.mid"
        self.pitch_diff = None
        self.timestamps = None

        mid = MidiFile(self.melodyfile)
        track = mid.tracks[0]
        for msg in track:
            if msg.type == 'note_on':
                self.firstnote = msg.note
                break

    def preprocess(self):
        self.fetchMelodyPitchDiff()
        self.fetchTimestamps()

    def setFile(self, file):
        self.file = SONG_PATH + file

    def fetchMelodyPitchDiff(self):
        """
        Outputs list of intervals' semitone difference
        """
        file = open(SONG_PATH + self.name + "_stripped.txt", 'r')
        pitch_diff_string = file.readline()
        pitch_diff = (pitch_diff_string.strip()).split(",")
        file.close()
        pitch_diff = [float(i) for i in pitch_diff]
        self.pitch_diff = pitch_diff

    def fetchTimestamps(self):
        """
        Outputs list of intervals' semitone difference
        """
        file = open(SONG_PATH + self.name + "_timestamps.txt", 'r')
        timestamps_string = file.readline()
        timestamps = (timestamps_string.strip()).split(",")
        file.close()
        timestamps = [float(i) for i in timestamps]
        self.timestamps = timestamps

    def getMIDI(self):
        return self.file

    def getWAV(self):
        return self.wav



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
            self.songs[songname].preprocess()

    def getMelody(self, songname):
        return self.songs[songname].pitch_diff

    def getAllMelody(self):
        melodydic = {}
        for songname in self.songs.keys():
            melodydic[songname] = self.songs[songname].pitch_diff
        return melodydic

    def getFirstNote(self, songname):
        return self.songs[songname].firstnote

    def getAllFirstNode(self):
        firstnotedic = {}
        for songname in self.songs.keys():
            #firstnotedic[songname] = self.songs[songname].firstnote
            firstnotedic[songname] = 60
        return firstnotedic

    def getTimestamps(self, songname):
        return self.songs[songname].timestamps

    def getAllTimestamps(self):
        timestampsdic = {}
        for songname in self.songs.keys():
            timestampsdic[songname] = self.songs[songname].timestamps
        return timestampsdic

    def getMIDI(self, songname):
        return self.songs[songname].getMIDI()

    def getWAV(self, songname):
        return self.songs[songname].getWAV()

if __name__ == "__main__":

    allSongNames = ["twinkle","london_bridge","three_blind_mice","boat","lullaby","mary_had_a_little_lamb"]

    songdb = SongDatabase(allSongNames)
    songdb.preprocessMelodies()


    # Example use
    # melody = songdb.getMelody("three_blind_mice")
    # timestamps = songdb.getTimestamps("three_blind_mice")
    # firstNote = songdb.getFirstNote("three_blind_mice")
    # WAVfile = songdb.getWAV("three_blind_mice")
    # MIDIfile = songdb.getMIDI("three_blind_mice")

    print(songdb.getAllMelody())
    print(songdb.getAllFirstNode())
    print(songdb.getAllTimestamps())
