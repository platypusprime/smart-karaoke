from queue import Queue
from threading import Thread, Condition

import librosa
import numpy

class Sound(object):
    """ Sound object which can be read chunk by chunk. """

    def __init__(self, y, sr, chunk_size=1024):
        """
        :param array y: numpy array representing the audio data
        :param int sr: samplerate
        :param int chunk_size: size of each chunk (default 1024)
        You also have access two properties:
            * pitch_shift (real time pitch shifting)
            * time_stretch (real time time-scale without pitch modification)
            * volume (real time volume level)
        Both can be tweaked simultaneously.
        """
        self.y, self.sr = y.astype(dtype='float32'), sr
        self.chunk_size = chunk_size

        self._init_stretching()

        self.loop = False

        # Effect properties
        self.pitch_shift = 0
        self.stretch_factor = 1.0
        self.volume = 1.0

    def resample(self, target_sr):
        """ Returns a new sound with a samplerate of target_sr. """
        y_hat = librosa.core.resample(self.y, self.sr, target_sr)
        return Sound(y_hat, target_sr)

    # IO methods

    def as_ipywidget(self):
        """ Provides an IPywidgets player that can be used in a notebook. """
        from IPython.display import Audio

        return Audio(data=self.y, rate=self.sr)

    @classmethod
    def from_file(cls, filename, sr=22050):
        """ Loads an audiofile, uses sr=22050 by default. """
        y, sr = librosa.load(filename, sr=sr)
        return cls(y, sr)

    # Chunk iterator

    @property
    def playing(self):
        """ Whether the sound is currently played. """
        return self._playing

    @playing.setter
    def playing(self, value):
        if value and hasattr(self, '_it'):
            self._reset()

        self._playing = value

    @property
    def chunks(self):
        """ Returns a chunk iterator over the sound. """
        if not hasattr(self, '_it'):
            class ChunkIterator(object):
                def __iter__(iter):
                    return iter

                def __next__(iter):
                    try:
                        chunk = self._next_chunk()
                    except StopIteration:
                        if self.loop:
                            self._init_stretching()
                            return iter.__next__()

                        raise

                    return chunk
                next = __next__

            self._it = ChunkIterator()

        return self._it

    def _next_chunk(self):
        chunk = self._time_stretcher(self.stretch_factor)

        if numpy.round(self.pitch_shift, 1) != 0:
            chunk = self.pitch_shifter(chunk, self.pitch_shift)
        chunk *= self.volume

        if len(chunk) != self.chunk_size:
            raise StopIteration

        return chunk

    # Effects

    def pitch_shifter(self, chunk, shift):
        """ Pitch-Shift the given chunk by shift semi-tones. """
#        freq = numpy.fft.rfft(chunk)
#
#        N = len(freq)
#        shifted_freq = numpy.zeros(N, freq.dtype)
#
#        S = numpy.round(shift if shift > 0 else N + shift, 0)
#        s = N - S
#
#        shifted_freq[:S] = freq[s:]
#        shifted_freq[S:] = freq[:s]
#
#        shifted_chunk = numpy.fft.irfft(shifted_freq)

        shifted_chunk = librosa.effects.pitch_shift(chunk, self.sr, shift)

        return shifted_chunk.astype(chunk.dtype)

    def _reset(self):
        del self._it
        self._init_stretching()

    def _init_stretching(self):
        # Resp. index of current audio chunk and computed phase
        self._i1, self._i2 = 0, 0
        self._N, self._H = self.chunk_size, int(self.chunk_size / 4)

        self._win = numpy.hanning(self._N)
        self._phi = numpy.zeros(self._N, dtype=self.y.dtype)
        self._sy = numpy.zeros(len(self.y), dtype=self.y.dtype)

        if not hasattr(self, '_sf'):
            self.stretch_factor = 1.0

        self._zero_padding()

    def _zero_padding(self):
        padding = int(numpy.ceil(len(self.y) / self.stretch_factor + self._N) - len(self._sy))
        if padding > 0:
            self._sy = numpy.concatenate((self._sy,
                                          numpy.zeros(padding, dtype=self._sy.dtype)))

    @property
    def stretch_factor(self):
        return self._sf

    @stretch_factor.setter
    def stretch_factor(self, value):
        self._sf = value
        self._zero_padding()

    def _time_stretcher(self, stretch_factor):
        """ Real time time-scale without pitch modification.
            :param int i: index of the beginning of the chunk to stretch
            :param float stretch_factor: audio scale factor (if > 1 speed up the sound else slow it down)
            .. warning:: This method needs to store the phase computed from the previous chunk. Thus, it can only be called chunk by chunk.
        """
        start = self._i2
        end = min(self._i2 + self._N, len(self._sy) - (self._N + self._H))

        if start >= end:
            raise StopIteration

        # The not so clean code below basically implements a phase vocoder
        out = numpy.zeros(self._N, dtype=numpy.complex)

        while self._i2 < end:
            if self._i1 + self._N + self._H > len(self.y):
                raise StopIteration

            a, b = self._i1, self._i1 + self._N
            S1 = numpy.fft.fft(self._win * self.y[a: b])
            S2 = numpy.fft.fft(self._win * self.y[a + self._H: b + self._H])

            self._phi += (numpy.angle(S2) - numpy.angle(S1))
            self._phi = self._phi - 2.0 * numpy.pi * numpy.round(self._phi / (2.0 * numpy.pi))

            out.real, out.imag = numpy.cos(self._phi), numpy.sin(self._phi)

            self._sy[self._i2: self._i2 + self._N] += self._win * numpy.fft.ifft(numpy.abs(S2) * out).real

            self._i1 += int(self._H * self.stretch_factor)
            self._i2 += self._H

        chunk = self._sy[start:end]

        if stretch_factor == 1.0:
            chunk = self.y[start:end]

        return chunk
#        return librosa.effects.time_stretch(self.y[start:end], stretch_factor)

class Sampler(object):
    """ Sampler used to play, stop and mix multiple sounds.
        .. warning:: A single sampler instance should be used at a time.
    """

    def __init__(self, sr=22050, backend='sounddevice'):
        """
        :param int sr: samplerate used - all sounds added to the sampler will automatically be resampled if needed (- his can be a CPU consumming task, try to use sound with all identical sampling rate if possible.
        :param str backend: backend used for playing sound. Can be either 'sounddevice' or 'dummy'.
        """
        self.sr = sr
        self.sounds = []

        self.chunks = Queue(1)
        self.chunk_available = Condition()

        if backend == 'dummy':
            from .dummy_stream import DummyStream
            self.BackendStream = DummyStream
        elif backend == 'sounddevice':
            from sounddevice import OutputStream
            self.BackendStream = OutputStream
        else:
            raise ValueError("Backend can either be 'sounddevice' or 'dummy'")

        # TODO: use a process instead?
        self.play_thread = Thread(target=self.run)
        self.play_thread.daemon = True
        self.play_thread.start()

    def play(self, sound):
        """ Adds and plays a new Sound to the Sampler.
            :param sound: sound to play
            .. note:: If the sound is already playing, it will restart from the beginning.
        """
        if self.sr != sound.sr:
            raise ValueError('You can only play sound with a samplerate of {} (here {}). Use the Sound.resample method for instance.', self.sr, sound.sr)

        if sound in self.sounds:
            self.remove(sound)

        with self.chunk_available:
            self.sounds.append(sound)
            sound.playing = True

            self.chunk_available.notify()

    def remove(self, sound):
        """ Remove a currently played sound. """
        with self.chunk_available:
            sound.playing = False
            self.sounds.remove(sound)

    # Play loop

    def next_chunks(self):
        """ Gets a new chunk from all played sound and mix them together. """
        with self.chunk_available:
            while True:
                playing_sounds = [s for s in self.sounds if s.playing]

                chunks = []
                for s in playing_sounds:
                    try:
                        chunks.append(next(s.chunks))
                    except StopIteration:
                        s.playing = False
                        self.sounds.remove(s)

                if chunks:
                    break

                self.chunk_available.wait()

            return numpy.mean(chunks, axis=0)

    def run(self):
        """ Play loop, i.e. send all sound chunk by chunk to the soundcard. """
        self.running = True

        def chunks_producer():
            while self.running:
                self.chunks.put(self.next_chunks())

        t = Thread(target=chunks_producer)
        t.start()

        with self.BackendStream(samplerate=self.sr, channels=1) as stream:
            while self.running:
                stream.write(self.chunks.get())

if __name__ == '__main__':
    sampler = Sampler()
    sound = Sound.from_file('a2002011001-e02.wav')
    sampler.play(sound)
