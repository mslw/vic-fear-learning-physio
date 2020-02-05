import numpy as np
from scipy import signal


def preprocess_emg(raw_emg, bandpass=True, rectify=True, smooth=True):

    s = raw_emg

    if bandpass:
        b, a = signal.iirfilter(4, [0.028, 0.500], btype='bandpass', analog=False, ftype='butter', output='ba')
        s = signal.filtfilt(b, a, raw_emg)

    if rectify:
        s = np.abs(s)

    if smooth:
        h = signal.firwin(101, 0.040)
        s = signal.filtfilt(h, np.array([1.]), s)

    return s


def extract_trials(signal_array, onsets, samples_before=100, samples_after=300):
    """
    Extract trials from a given channel, relative to a given marker value.
    :param signal_array: 1-D array with channel data
    :param onsets: event onsets (in samples)
    :param samples_before: number of samples taken before the marker
    :param samples_after: number of samples taken after the marker
    :return: trials_array: array containing trials, with shape (trials x samples)
    """
    window_size = samples_before + samples_after
    n_trials = len(onsets)
    trials_array = np.zeros((n_trials, window_size))

    for n in range(n_trials):
        s = onsets[n]
        trials_array[n, :] = signal_array[s - samples_before:s + samples_after]

    return trials_array
