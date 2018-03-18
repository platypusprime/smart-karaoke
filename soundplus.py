import numpy as np
from aupyom import Sound
import phasevocoder

#TODO ease in playback adjustments

class SoundPlus(Sound):

    def __init__(self, y, sr, chunk_size=1024):
        self._init_offset = 0
        super().__init__(y, sr, chunk_size)

    def _init_stretching(self):
        super()._init_stretching()
        self._i1, self._i2 = self._init_offset, self._init_offset

        # variables for smooth volume changes
        self._volume = 1.0
        self._volume_cur = 0.0
        self._volume_orig = 0.0
        self._volume_step = 0
        self._volume_steps = 25

    def _next_chunk(self):
        # calculate adjustment factors
        shift_factor = 2.0 ** (1.0*self.pitch_shift / 12.0)
        adj_stretch_factor = self.stretch_factor / shift_factor

        # apply playback modification
        chunk = super()._time_stretcher(adj_stretch_factor)
        if np.round(self.pitch_shift, 1) != 0:
            chunk = phasevocoder.speedx(chunk, shift_factor)

        # apply volume multiplier
        chunk *= self._volume_cur

        # exponentially adjust volume
        # self.cur_volume = self.cur_volume + (self._volume - self._volume_cur) * 0.2

        # sinusoidally adjust volume
        if self._volume_step <= self._volume_steps:
            self._volume_cur = self._ease_sinusoidal(orig      = self._volume_orig,
                                                     target    = self._volume,
                                                     step      = self._volume_step,
                                                     max_steps = self._volume_steps)
            self._volume_step += 1

        return chunk

    def _ease_sinusoidal(self, orig, target, step, max_steps):
        adj = target - orig
        progress = step / max_steps
        cur_adj = adj * (1 - np.cos(progress * np.pi)) / 2.0
        return orig + cur_adj

    def navigate(self, offset):
        self._init_offset = offset

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value
        self._volume_orig = self._volume_cur
        self._volume_step = 0

if __name__ == '__main__':
    from aupyom import Sampler
    import sys

    sampler = Sampler()
    sound = SoundPlus.from_file(sys.argv[1])
    print("done loading sound")
    sound.navigate(100000)
    sampler.play(sound)
