from ecutils.eventhandler import EventCollection
from ecutils.eda import Trial
from ecutils.fix_assignment import fix_assignment

import cvxEDA

import scipy.signal as ss
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import matplotlib.patches as mpatch
import argparse
import re
import glob
import pandas
import os


def smart_annotate(axis, first, last, text, color):
    """Adds rectangle with annotation above the plot.
    The rectangle encompasses all values between first and last (inclusive)
    with a fractional offset."""

    trans = mtransforms.blended_transform_factory(
        axis.transData, axis.transAxes)

    # predefined constants
    offset = 0.4
    height = 0.1
    start_y = 1.02

    # extend past selected points
    start_x = first - offset
    end_x = last + offset
    width = end_x - start_x

    rec = mpatch.Rectangle((start_x, start_y), width, height,
                           transform=trans, color=color)
    rec.set_clip_on(False)

    axis.add_artist(rec)
    axis.text(start_x + width / 2, start_y + height / 2, text,
              transform=trans, ha='center', va='center')


def extract_phase(signal, events, start_mrk, stop_mrk):
    phase_start = events.samples_for_marker(start_mrk)[0]
    phase_end = events.samples_for_marker(stop_mrk)[0]
    phase_signal = signal[phase_start:phase_end]
    phase_events = events.events_between_events(start_mrk, stop_mrk)
    phase_ec = EventCollection.from_list(phase_events, reset_samples=True)

    return phase_signal, phase_ec


def process_phase(all_signal, all_events, start_mrk, stop_mrk,
                  n_fragments, fs):

    # hardcoded: length of trial and baseline
    n_s = (9+10)*fs  # take 9 seconds of CS and 10 seconds of fix
    n_b_s = 2*fs

    # extract signal and events for the requested parts
    signal, events = extract_phase(all_signal, all_events, start_mrk, stop_mrk)

    # decompose
    [r, p, t, l, d, e, obj] = cvxEDA.cvxEDA(signal, 1/fs)

    # divide the tonic signal into fragments and calculate SCL
    fragments = np.array_split(t, n_fragments)
    levels = [a.mean() for a in fragments]

    # extract trials
    trials = []
    onsets_cs = events.samples_for_marker(1) + events.samples_for_marker(2)
    onsets_cs.sort()

    for onset in onsets_cs:
        trial_events = events.events_between_samples(onset, onset+n_s)
        trials.append(Trial(events=trial_events,
                            n_samples=n_s,
                            n_bl_samples=n_b_s,
                            fs=fs,
                            signal=r,
                            smna=p,
                            ))

    return levels, trials


def score_trials(list_of_trials, name):
    # score trials

    scores = []
    for n, trial in enumerate(list_of_trials):
        stimulus = 'CS+' if 1 in trial.event_values else 'CS-'
        amplitude, peak_time = trial.score_eir(
            onset=0,
            duration=6,
            baseline_length=2)

        scores.append(
            {
                'stimulus': '{} {}'.format(name, stimulus),
                'trial': n,
                'amplitude': amplitude,
            })

        # in obs stage, score reaction to US (or US absent), but only for CS+
        if (name == 'obs' and set(trial.event_values).isdisjoint({4, 5, 6})
                and 1 in trial.event_values):

            stimulus = 'US present' if 8 in trial.event_values else 'US absent'
            amplitude, peak_time = trial.score_eir(
                onset=7.5,
                duration=6,
                baseline_length=2)

            scores.append(
                {
                    'stimulus': '{} {}'.format(name, stimulus),
                    'trial': n,
                    'amplitude': amplitude
                })

    return scores


def plot_trials(nrows, ncols, trials, fname):
    fig, axs = plt.subplots(nrows, ncols, figsize=(12.8, 7.2), sharey=True)
    pmax = np.max([trial.smna.max() for trial in trials])
    for i, ax in enumerate(axs.flat):
        tx = ax.twinx()
        tx.set_ylim(0, pmax)
        trials_ofl[i].plot(ax, tx)
    fig.savefig(fname)
    plt.close(fig)


def save_scores(list_of_scores, subject_code):
    df_directory = os.path.join('out', 'stat_data', 'eda')
    df = pandas.DataFrame.from_records(list_of_scores)

    # fix CS+ / CS- labels
    # for some subjects versions were mismatched between OFL and DE
    fix_assignment(subject_code, df)

    if not os.path.exists(df_directory):
        os.makedirs(df_directory)
    df_filename = os.path.join(df_directory, subject_code + '.pickle')
    df.to_pickle(df_filename)


# potential TODO: plot entire OFL / DE signal

# optionally stop calculations after n subjects (useful for testing)
parser = argparse.ArgumentParser()
parser.add_argument('--stop_after', help='process at most this many subjects',
                    type=int)
args = parser.parse_args()

# constants
fs = 25
fname_pattern = re.compile('([A-Z]+)_eda.npy')

# data files
data_files = glob.glob('out/raw_data/[A-Z]*_eda.npy')

# output directory for figures
fig_directory = os.path.join('out', 'figures', 'eda')
if not os.path.exists(fig_directory):
    os.makedirs(fig_directory)

all_levels = []
fuse = args.stop_after  # stop after this many subjects - for testing

for data_file in data_files:
    eda = np.load(data_file)

    event_file = data_file.replace('_eda.npy', '_events.txt')
    event_collection = EventCollection.from_txt(event_file)

    code = re.search(fname_pattern, data_file).group(1)

    # downsample events
    event_collection.downsample(80)  # 25 * 8 * 5 * 2

    # downsample eda
    eda = ss.decimate(eda, 8)
    eda = ss.decimate(eda, 5)
    eda = ss.decimate(eda, 2)

    # fix events
    if re.search(fname_pattern, data_file).group(1) == 'RAZVAJ':
        # see notebook for rationale
        # no more marker problems affect the analysis
        if event_collection.all_events()[1].value == 1:
            event_collection.remove_at_index(1)
        if event_collection.events_between_events(13, 14)[1].value == 2:
            event_collection.events_between_events(13, 14)[1].value = 7

    # extract SCLs and trials for all three stages of the experiment

    levels_rest, _ = process_phase(
        eda, event_collection, 11, 12, 1, fs)
    levels_ofl, trials_ofl = process_phase(
        eda, event_collection, 13, 14, 6, fs)
    levels_de, trials_de = process_phase(
        eda, event_collection, 15, 16, 3, fs)

    # gather skin conductance levels
    levels = np.array(levels_rest + levels_ofl + levels_de)
    all_levels.append(levels)

    # score trials
    scores_ofl = score_trials(trials_ofl, 'obs')
    scores_de = score_trials(trials_de, 'direct')

    # plot trials
    plot_trials(8, 6, trials_ofl,
                fname=os.path.join(fig_directory, code + '_trials_OFL.png'))
    plot_trials(6, 4, trials_de,
                fname=os.path.join(fig_directory, code + '_trials_DE.png'))

    # gather & save trial scores
    scores = scores_ofl + scores_de
    for score in scores:
        score['code'] = code
    save_scores(scores, code)

    # do not run all subjects - for development
    if fuse is not None:
        fuse -= 1
        if fuse == 0:
            break


# SCL - stack all subjects and make relative to first column
scl = np.stack(all_levels)
baseline = scl[:, 0]
scl_rel = scl - baseline[:, np.newaxis]

# --- SCL plot ---
fig = plt.figure()
ax = fig.gca()
# plot individual lines
for i in range(scl_rel.shape[0]):
    ax.plot(scl_rel[i, :],
            marker='o', linestyle='solid', color='black', alpha=0.2)

# plot the mean
ax.plot(np.mean(scl_rel, axis=0), linewidth=4.)

# boxes with names of phases
smart_annotate(ax, first=0, last=0, text='RS', color=plt.cm.Pastel2(7))
smart_annotate(ax, first=1, last=6, text='Observational Fear Learning',
               color=plt.cm.Pastel2(6))
smart_annotate(ax, first=7, last=9, text='Direct Expression',
               color=plt.cm.Pastel2(5))

# ticks & labels
ax.set_xticks([])
ax.set_xlabel('Time (blocks)')
ax.set_ylabel('Relative SCL (µS)')
# ax.set_ylim(-1.54, 7.05)  # to match the old plot
plt.show()
# --- end of SCL plot ---
