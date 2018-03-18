from scipy.io import wavfile
import numpy as np

def speedx(snd_array, factor):
    """
    Speeds up or slows down a given sound array by some factor. Does this by
    skipping or repeating elements in the incoming array to cut or pad its
    runtime.

    Parameters
    ----------
    snd_array : ndarray
        The original sound data.
    factor : number
        The speed-up or slow-down factor. Essentially, the speed of the sound
        will be multiplied by this number.
    Returns
    -------
    spd_array : ndarray
        An array of the same type as `snd_array`, containing the speed-changed
        output.
    """

    indices = np.arange(0, len(snd_array), factor)
    # addresses issue where NP rounds to nearest even integer for x.5
    indices = np.round(np.where(indices % 2 == 1.5, indices - 0.1, indices))
    # cap indices at len - 1
    indices = np.where(indices < len(snd_array), indices, len(snd_array) - 1)
    # repeat or skip sound indices to create the speed change effect
    return snd_array[indices.astype(int)]


def stretch(snd_array, factor, window_size=2**13, h=2**11):
    """
    Stretches or compresses a given sound array, by some factor.
    """

    if (snd_array == 0).all():
        print("all frames zero, returning resized zero array")
        return np.zeros((int(snd_array.shape[0]*factor), snd_array.shape[1]), dtype='int16')

    phase = np.zeros(window_size)
    hanning_window = np.hanning(window_size)
    result = np.zeros(int(len(snd_array) / factor) + window_size)
    shift = np.zeros(window_size, dtype=np.complex)

    for i in np.arange(0, len(snd_array) - (window_size + h), h*factor):
        # Two potentially overlapping subarrays
        a1 = hanning_window * snd_array[int(i): int(i + window_size)]
        a2 = hanning_window * snd_array[int(i + h): int(i + window_size + h)]

        # The spectra of these arrays
        s1 = np.fft.fft(a1)
        s2 = np.fft.fft(a2)

        # Rephase all frequencies
        phase = phase + np.angle(s2) - np.angle(s1)
        phase = phase % (2*np.pi)
        shift.real, shift.imag = np.cos(phase), np.sin(phase)

        a2_rephased = np.fft.ifft(np.abs(s2)*shift)
        a2_rephased = hanning_window * a2_rephased.real
        i2 = int(i/factor)
        result[i2: i2 + window_size] += a2_rephased

    # normalize (16bit)
    if result.max() != 0:
        result = ((2**(16-4)) * result/result.max())

    return result.astype('int16')


def pitchshift(snd_array, n, window_size=2**13, h=2**11):
    """
    Changes the pitch of a sound by ``n`` semitones.
    """

    tracks = snd_array.shape[1]

    if tracks == 1:
        factor = 2**(1.0 * n / 12.0)
        stretched = stretch(snd_array, 1.0/factor, window_size, h)
        return speedx(stretched[window_size:], factor)

    elif tracks == 2:
        t1_mod = pitchshift(snd_array.T[0], n, window_size, h)
        t2_mod = pitchshift(snd_array.T[1], n, window_size, h)
        return np.stack((t1_mod, t2_mod), 0).T

    return snd_array

if __name__ == '__main__':
    fps, sound = wavfile.read("inputs/playback/frozen.wav")
    sound_mod = stretch(sound.T[0], 1.0/1.2, window_size=2**9, h=2**7)
    wavfile.write("frozen_sp=1.2x,w=512,h=128.wav", fps, sound_mod)
