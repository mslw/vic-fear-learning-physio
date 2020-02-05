import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas
import re

from ecutils.eventhandler import EventCollection
from ecutils.emg import preprocess_emg
from ecutils.fix_assignment import fix_assignment


def count_events(list_of_events, values):
    result = []
    for v in values:
        result.append(sum(e.value == v for e in list_of_events))
    return result


def score_trials(list_of_events, x_raw, x_prep, subject_code, stim_prefix):
    """ Given a list of events, score CS+ / CS- / fix startle trials
    Assumes fs = 2000 Hz
    """
    table_contents = []
    max_trials = max(count_events(list_of_events, [4, 5, 6]))
    fragments = np.zeros((2, 3, max_trials, 400))
    # dimensions: signal type, trial type, trial number, samples

    # figure out what trial are we dealing with
    counter_plus, counter_minus, counter_fix = 0, 0, 0
    for event in list_of_events:
        if event.value == 5:
            stimulus = '{} CS+'.format(stim_prefix)
            counter_plus += 1
            trial = counter_plus
            t_type = 1
        elif event.value == 6:
            stimulus = '{} CS-'.format(stim_prefix)
            counter_minus += 1
            trial = counter_minus
            t_type = 2
        elif event.value == 4:
            stimulus = '{} fix'.format(stim_prefix)
            counter_fix += 1
            trial = counter_fix
            t_type = 0
        else:
            continue

        # calculate the amplitude
        baseline = np.mean(x_prep[event.sample - 100: event.sample])
        peak = np.max(x_prep[event.sample + 40: event.sample + 240])

        result = peak - baseline if peak > baseline else 0

        # store the signal fragment for plotting (longer fragment than above)
        frag_raw = x_raw[event.sample - 100: event.sample + 300]
        frag_prep = x_prep[event.sample - 100: event.sample + 300]
        # using trial minus one as index because trials start from 1
        fragments[0, t_type, trial - 1, :] = frag_raw
        fragments[1, t_type, trial - 1, :] = frag_prep

        # save the amplitude (row in data frame)
        row_content = {
            'code': subject_code,
            'stimulus': stimulus,
            'trial': trial,
            # 'peak_time': None,
            'amplitude': result,
        }

        table_contents.append(row_content)

    return table_contents, fragments


def plot_grid(trial_arr, out_folder, subject_code):

    s_before = 100
    s_after = 300
    t_axis = np.linspace(-s_before/2, s_after/2, s_before + s_after)

    y_max = 0.20  # uniform for all subjects, should fit most reactions

    n_trials = trial_arr.shape[2]
    n_rows, n_cols = 3, int(np.ceil(n_trials/3))
    fig, axs = plt.subplots(n_rows, n_cols, sharex='all', sharey='all',
                            figsize=(24, 12))

    for c_index, c_name in enumerate(['fix', 'CS+', 'CS-']):
        for n, ax in enumerate(axs.flat):
            ax.clear()
            ax.plot(t_axis, trial_arr[0, c_index, n, :])  # raw
            ax.plot(t_axis, trial_arr[1, c_index, n, :])  # prep

            ax.set_title(str(n + 1))
            ax.axvline(0, linestyle='--', color='black')
            ax.fill_between([20, 120], 0, y_max, alpha=0.3)
            ax.set_ylim(0, y_max)

        fig.suptitle(c_name)
        c_nicename = c_name.replace('+', '_plus').replace('-', '_minus')

        fig.savefig(os.path.join(
            out_folder, '{}_{}'.format(subject_code, c_nicename)))


# data files
data_files = glob.glob('out/raw_data/[A-Z]*_emg.npy')
fname_pattern = re.compile('([A-Z]+)_emg.npy')

for data_file in data_files:
    event_file = data_file.replace('_emg.npy', '_events.txt')
    subject = re.search(fname_pattern, data_file).group(1)

    print(subject)

    event_collection = EventCollection.from_txt(event_file)
    emg_raw = np.load(data_file)
    emg_preprocessed = preprocess_emg(emg_raw)
    emg_rough = preprocess_emg(emg_raw, smooth=False)  # plot this & smoothed

    rows_ofl, frag_ofl = score_trials(
        list_of_events=event_collection.events_between_events(13, 14),
        x_raw=emg_rough,
        x_prep=emg_preprocessed,
        subject_code=subject,
        stim_prefix='obs'
        )

    rows_de, frag_de = score_trials(
        list_of_events=event_collection.events_between_events(15, 16),
        x_raw=emg_rough,
        x_prep=emg_preprocessed,
        subject_code=subject,
        stim_prefix='direct'
        )

    df = pandas.DataFrame(
        data=rows_ofl + rows_de,
        columns=('code', 'stimulus', 'trial', 'amplitude')
        )

    # fix CS+ / CS- labels
    # for some subjects versions were mismatched between OFL and DE
    fix_assignment(subject, df)

    trials = np.concatenate([frag_ofl, frag_de], axis=2)

    df_directory = os.path.join('out', 'stat_data', 'emg')
    if not os.path.exists(df_directory):
        os.makedirs(df_directory)
    df_filename = os.path.join(df_directory, subject + '.pickle')
    df.to_pickle(df_filename)

    fig_directory = os.path.join('out', 'figures', 'emg')
    if not os.path.exists(fig_directory):
        os.makedirs(fig_directory)
    plot_grid(trials, fig_directory, subject)
