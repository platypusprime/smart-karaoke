'''
Class for playback of .wav files, with live adjustments to speed, pitch, and
volume. Extends aupyom to perform playback modification and uses LibROSA to
load wav files.
'''

from soundplus import SoundPlus
from samplercpy import Sampler

class WavPlayer(object):

    def __init__(self, **files):
        '''
        Creates a player for the specified .wav file with fixed time stretch
        and pitch shift characteristics.

        Parameters
        ----------
        files : string kvarargs
            The file paths of all .wav files to load
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

        self._curr_file = None
        self.sounds = {}
        for song, wav in files.items():
            print("Loading %s from %s" % (song, wav))
            self.sounds[song] = SoundPlus.from_file(wav)
        self.sound = None
        self.sampler = Sampler(sr=44100)

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

    @property
    def curr_file(self):
        return self._curr_file

    @curr_file.setter
    def curr_file(self, value):
        print("Setting song to %s" % (value))
        self._curr_file = value
        self.sound = self.sounds.get(self._curr_file, None)

if __name__ == '__main__':
    # example usage
    proc = WavPlayer(twinkle="musicbank/twinkle.wav")
    proc.curr_file = "twinkle"
    proc.play()
