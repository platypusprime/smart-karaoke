'''
Class for playback of .wav files, with live adjustments to speed, pitch, and
volume. Extends aupyom to perform playback modification and uses LibROSA to
load wav files.
'''

from soundplus import SoundPlus
from aupyom import Sampler

class WavPlayer(object):

    def __init__(self, file, stretch=1, shift=0, offset=0):
        '''
        Creates a player for the specified .wav file with fixed time stretch
        and pitch shift characteristics.

        Parameters
        ----------
        file : string
            The file path of the .wav file to play
        stretch : number, optional
            The time-stretch factor. A stretch value of 1.0 will result in a
            playback at the original speed.
        shift : number, optional
            The pitch shift amount, in semitones. A shift value of 0.0 will
            result in a playback at the original pitch.
        offset : number, optional
            The initial frame offset of the playback. An offset value of
            0 will result in playback from the beginning of the file.
        '''

        self.sampler = Sampler(sr=44100)
        self.sound = SoundPlus.from_file(file)

    def navigate(self, offset):
        self.sound.navigate(offset)

    def play(self):
        self.sampler.play(self.sound)

    def stop(self):
        self.sound.playing = False

    @property
    def volume(self):
        return self.sound.volume

    @volume.setter
    def volume(self, value):
        self.sound.volume = value

    @property
    def pitch_shift(self):
        return self.sound.pitch_shift

    @pitch_shift.setter
    def pitch_shift(self, value):
        self.sound.pitch_shift = value

    @property
    def time_stretch(self):
        return self.sound.stretch_factor

    @time_stretch.setter
    def time_stretch(self, value):
        self.sound.stretch_factor = value

if __name__ == '__main__':
    # example usage
    proc = WavPlayer("toms_diner.wav")
    proc.play()
#    proc = WavPlayer("toms_diner.wav", stretch=1.5)
#    proc = WavPlayer("toms_diner.wav", shift=2)
#    proc = WavPlayer("toms_diner.wav", stretch=0.9, shift=-0.1)
