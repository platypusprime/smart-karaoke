import numpy as np
from aupyom import Sound
import phasevocoder

#TODO implement initial offset
#TODO ease in volume adjustments
#TODO ease in playback adjustments


class SoundPlus(Sound):

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

if __name__ == '__main__':
    from aupyom import Sampler
    import sys

    sampler = Sampler()
    sound = SoundPlus.from_file(sys.argv[1])
    print("done loading sound")
    sampler.play(sound)
