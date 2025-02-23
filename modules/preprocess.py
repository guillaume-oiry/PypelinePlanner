# License: BSD-3-Clause
# Copyright the MNE-Python contributors.

# Packages

import os
import sys
import mne

import _b_event_editing as _b_


# Modules

def EPICE_minimal_preprocessing(file_path, parameters, info):
    
    # Scrap parameters
    low_freq = parameters['LOW_FREQ']
    high_freq = parameters['HIGH_FREQ']
    notch_filter = parameters['NOTCH_FILTER']
    bad_channels = parameters['BAD_CHANNELS']
    
    raw = mne.io.read_raw(file_path, preload=True)
    rec = extract_rec(raw)
    raw = rereferencing(raw)
    raw = min_filtering(raw, l_freq = low_freq, h_freq = high_freq, notch_f = notch_filter)
    raw.info['bads'] = bad_channels[rec]
    
    raw_dict = {rec : {'raw' : {'no_cleaning' : {'no_analysis' : {'data': raw}}}}}
    
    return raw_dict

## Side functions

def extract_rec(raw):
    file_name = os.path.basename(raw.filenames[0])
    rec = os.path.splitext(file_name)[0]
    return rec

def extract_info(raw):
    file_name = os.path.basename(raw.filenames[0])
    dot_split = os.path.splitext(file_name)
    parts = dot_split[0].split('_')

    if len(parts) == 4:
        # Create the dictionary with the required elements
        file_info = {
            'sub': parts[0].split('-')[1],
            'ses': parts[1].split('-')[1],
            'task': parts[2].split('-')[1],
        }
        print(file_info)
    else:
        print("Unexpected filename format. Please check the input.")
        sys.exit()
    
    return file_info

def extract_info_from_rec_name(rec_name):
    parts = rec_name.split('_')
    
    rec_info = {
        'sub': parts[0].split('-')[1],
        'ses': parts[1].split('-')[1],
        'task': parts[2].split('-')[1],
    }
    
    return rec_info

def mapping(raw, new_ch_names = ['Fp1','Fp2','Fz','Cz','Pz','O1','O2','M1']):

    if 'TimeStamp' in raw.info['ch_names'] :
        raw.drop_channels(['TimeStamp'])

    old_ch_names = raw.info['ch_names']

    if len(old_ch_names) == 8:
        mapping = dict(zip(old_ch_names, new_ch_names))
    
    raw.rename_channels(mapping)
    raw.set_montage('standard_1020')
    return raw

def rereferencing(raw):
    raw._data[:6, :] = raw._data[:6,:] - raw._data[7, :]/2
    raw.drop_channels('M1')
    return raw

def min_filtering(raw, l_freq = 0.1, h_freq = 40, notch_f = 50):
    raw.filter(l_freq, h_freq)
    raw.notch_filter(notch_f)
    return raw

