import bioread
import configparser
import numpy as np
import os

import ecutils.eventhandler

config = configparser.ConfigParser()
config.read('emocon_config.ini')
SOURCE_DIR = config['DEFAULT']['SOURCE_DIR']
OUT_FOLDER = 'out/raw_data'

file_names = os.listdir(SOURCE_DIR)
file_names = [f for f in file_names if f.endswith('.acq')]
file_names = [f for f in file_names if not f.startswith('._')]

if not(os.path.exists(OUT_FOLDER)):
    os.makedirs(OUT_FOLDER)

for f_name in file_names:
    data = bioread.read_file(os.path.join(SOURCE_DIR, f_name))

    print('Extracting from', f_name)
    ec = ecutils.eventhandler.EventCollection.from_acq(data)

    eda = data.named_channels['EDA100C'].data
    emg = data.named_channels['EMG100C'].data

    subject_code = os.path.splitext(f_name)[0]

    np.save(os.path.join(OUT_FOLDER, subject_code + '_eda'), eda)
    np.save(os.path.join(OUT_FOLDER, subject_code + '_emg'), emg)

    ec.to_txt(os.path.join(OUT_FOLDER, subject_code + '_events.txt'))
