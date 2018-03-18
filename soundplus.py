import numpy as np
from aupyom import Sound
import phasevocoder

#TODO ease in volume adjustments
#TODO ease in playback adjustments

class SoundPlus(Sound):

    def __init__(self, y, sr, chunk_size=1024):
        self._init_offset = 0
        super().__init__(y, sr, chunk_size)

    def _init_stretching(self):
        super()._init_stretching()
        self._i1, self._i2 = self._init_offset, self._init_offset

    def _next_chunk(self):
        # calculate adjustment factors
        shift_factor = 2.0 ** (1.0*self.pitch_shift / 12.0)
        adj_stretch_factor = self.stretch_factor / shift_factor

        # apply playback modification
        chunk = super()._time_stretcher(adj_stretch_factor)
        if np.round(self.pitch_shift, 1) != 0:
            chunk = phasevocoder.speedx(chunk, shift_factor)

        # apply volume multiplier
        chunk *= self.volume

        return chunk

    def navigate(self, offset):
        self._init_offset = offset

if __name__ == '__main__':
    from aupyom import Sampler
    import sys

    sampler = Sampler()
    sound = SoundPlus.from_file(sys.argv[1])
    print("done loading sound")
    sound.navigate(100000)
    sampler.play(sound)
