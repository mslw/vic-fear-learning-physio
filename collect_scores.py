import glob
import os
import numpy as np
import pandas
from scipy import stats
import re

emg_paths = glob.glob(os.path.join('out', 'stat_data', 'emg', '*.pickle'))
eda_paths = glob.glob(os.path.join('out', 'stat_data', 'eda', '*.pickle'))

pat = re.compile('([A-Z]+).pickle')

# subjects to exclude after visual inspection
exclude_emg = {'ESFMRF': 'Bad signal quality (noise)'}

# t-score emg amplitudes for each subject & gather together
print('Collecting EMG')
data_frames = []
for f in emg_paths:
    code = re.search(pat, f).group(1)
    raw = pandas.read_pickle(f)

    if code in exclude_emg:
        print('Excluding subject', code, exclude_emg[code])
    elif (raw.amplitude > 0.01).sum() < 6:
        # here, t-scores would be hard to interpret
        print('Excluding subject', code, 'Not enough measurable reactions')
    else:
        raw.amplitude = 50 + 10 * stats.zscore(raw.amplitude)
        data_frames.append(raw)

df = pandas.concat(data_frames, ignore_index=True)

# save both as pickle and csv
df.to_pickle(os.path.join('out', 'stat_data', 'emg.pickle'))
df.to_csv(os.path.join('out', 'stat_data', 'emg.csv'))


# gather together eda amplitudes
print('Collecting EDA')
data_frames = []
for f in eda_paths:
    code = re.search(pat, f).group(1)
    raw = pandas.read_pickle(f)

    q = raw.query('stimulus.str.startswith("direct") & amplitude.notna()')
    if q.shape[0] < 5:
        print('Excluding subject', code, 'Not enough DE reactions')
    else:
        raw.amplitude = np.log(1 + raw.amplitude/raw.amplitude.max())
        data_frames.append(raw)

df = pandas.concat(data_frames, ignore_index=True)
df.to_pickle(os.path.join('out', 'stat_data', 'eda.pickle'))
df.to_csv(os.path.join('out', 'stat_data', 'eda.csv'))
