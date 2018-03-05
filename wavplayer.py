'''
Class for playback of .wav files, with adjustments to speed and pitch. Uses
LibROSA to load wav files and apply audio transformations, and PyAudio to 
interface with system I/O.

Currently supports only non-real-time operation.
'''

import pyaudio
import librosa

class WavPlayer(object):

    def __init__(self, file, stretch=1, shift=0):
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
        '''
        
        self.y, self.sr = librosa.load(path=file, sr=None, mono=True)
        self.y_mod = librosa.effects.time_stretch(self.y, stretch)
        self.y_mod = librosa.effects.pitch_shift(self.y_mod, self.sr, shift)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=int(self.sr),
                output=True)
        
        self.stream.start_stream()
        self.stream.write(self.y_mod, self.y_mod.shape[0])
        self.stream.stop_stream()
        self.stream.close()

if __name__ == '__main__':
    # example usage
    proc = WavPlayer("toms_diner.wav")
    proc = WavPlayer("toms_diner.wav", stretch=1.5)
    proc = WavPlayer("toms_diner.wav", shift=2)
    proc = WavPlayer("toms_diner.wav", stretch=0.9, shift=-0.1)
