import configparser
import os
import pandas

config = configparser.ConfigParser()
config.read('emocon_config.ini')
BEHAV_DIR = config['DEFAULT']['BEHAV_DIR']

# contingency
contingency = pandas.read_csv(os.path.join(BEHAV_DIR, 'contingency.csv'),
                              index_col=0)
contingency.contingency_known = contingency.contingency_known.astype(bool)

# eda
data_path = os.path.join('out', 'stat_data', 'eda.pickle')
df = pandas.read_pickle(data_path)

df_w = (df
        .fillna(value=0)
        .groupby(['code', 'stimulus'])
        .amplitude
        .mean()
        .unstack()
        .join(contingency, how='left')
        )

df_w.to_csv(os.path.join('out', 'stat_data', 'eda_summary.csv'))

# emg
data_path = os.path.join('out', 'stat_data', 'emg.pickle')
emg = pandas.read_pickle(data_path)

emg_summary = (emg
               .groupby(['code', 'stimulus'])
               .amplitude
               .mean()
               .unstack()
               .join(contingency, how='left')
               )
print(emg_summary.head())
emg_summary.to_csv(os.path.join('out', 'stat_data', 'emg_summary.csv'))
