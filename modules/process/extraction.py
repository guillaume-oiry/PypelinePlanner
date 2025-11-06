# License: BSD-3-Clause
# Copyright the MNE-Python contributors.

# Packages

import mne
import pandas as pd
import copy

# Modules

def get_raw_crops_general(data, parameters, info):
    
    extract = {}
    
    #Scrap parameters
    timings_dict = parameters['TIMINGS_DICT']
    if isinstance(timings_dict, dict):
        timings_dict = parameters['TIMINGS_DICT']
    else :
        timings_dict = get_timings_dict(data)
    
    for name in timings_dict.keys() :
        
        data_copy = data.copy()
        
        if isinstance(timings_dict[name][0], float):
            crop = data_copy.crop(tmin = timings_dict[name][0],
                                 tmax = timings_dict[name][1])
        elif isinstance(timings_dict[name][0], int):
            crop = data_copy.crop(tmin = data.annotations.onset[timings_dict[name][0]],
                                 tmax = data.annotations.onset[timings_dict[name][1]])
        else:
            crop = data_copy.crop(tmin = timings_dict[name][0](data),
                                 tmax = timings_dict[name][1](data))
        
        extract[f'raw_{name}'] = {'no_cleaning':{'no_analysis' : {'data' : crop}}}

    return extract

def get_raw_crops_specific(data, parameters, info):
    
    extract = {}
    
    #Scrap parameters
    if isinstance(timings_dict, dict):
        timings_dict = parameters['TIMINGS_DICT'][info['rec']]
    else :
        timings_dict = get_timings_dict(data)
    
    for name in enumerate(timings_dict.keys()) :
        
        data_copy = data.copy()
        
        if isinstance(timings_dict[name][0], float):
            crop = data_copy.crop(tmin = timings_dict[name][0],
                                 tmax = timings_dict[name][1])
        elif isinstance(timings_dict[name][0], int):
            crop = data_copy.crop(tmin = data.annotations.onset[timings_dict[name][0]],
                                 tmax = data.annotations.onset[timings_dict[name][1]])
        
        extract[f'raw_{name}'] = {'no_cleaning':{'no_analysis' : {'data' : crop}}}

    return extract

def simple_epoching(data, parameters, info):
    
    extract = {}

    #Scrap parameters
    tmin=parameters['TMIN']
    tmax=parameters['TMAX']
    ptp_threshold=parameters['PTP_THRESHOLD']
    reject_flat=parameters['REJECT_FLAT']
    main_path=parameters['MAIN_PATH']
    add_df=parameters['ADD_DF']

    #display_annotations(data)
    
    events, event_id = mne.events_from_annotations(data)

    epochs = mne.Epochs(
        data, 
        events, 
        event_id, 
        tmin = tmin, 
        tmax = tmax,
        event_repeated='drop',
        reject=dict(eeg=ptp_threshold) if ptp_threshold != None else None,
        flat=dict(eeg=1e-6) if reject_flat == True else None,
        preload = True
        )

    if add_df == True :
        epochs.metadata = pd.read_csv(f'{main_path}/DATA/{info['rec'].replace('_eeg.fif', '_behav.csv')}', index_col=[0]).reset_index(drop=True)
    
    # RESET INDEX
    extract['epochs'] = {'no_cleaning':{'no_analysis' : {'data' : epochs}}}
    
    return extract

def subset_epoching(data, info, tmin, tmax, ptp_threshold, reject_flat, add_df, labels):
    
    extract = {}
    
    '''
    #Scrap parameters
    tmin = parameters['TMIN']
    tmax = parameters['TMAX']
    ptp_threshold = parameters['PTP_THRESHOLD']
    reject_flat = parameters['REJECT_FLAT']
    add_df = parameters['ADD_DF']
    labels = parameters['LABELS']
    '''
    
    events, event_id = mne.events_from_annotations(data)

    epochs = mne.Epochs(
        data,
        events,
        event_id,
        tmin = tmin,
        tmax = tmax,
        event_repeated='drop',
        reject_by_annotation=False,
        reject=dict(eeg=ptp_threshold) if ptp_threshold != None else None,
        flat=dict(eeg=1e-6) if reject_flat == True else None,
        preload = True
        )
    
    bad_epochs = epochs.drop_log
    
    for label_name, label in labels.items():
        epochs_extract = epochs[label].copy()
        if add_df == True :
            epochs_extract.metadata = pd.read_csv(f'{main_path}/DATA/{info['rec'].replace('_eeg', '_behav.csv')}', index_col=[0]).reset_index(drop=True)
        # RESET INDEX
        extract[f'epochs_{label_name}'] = epochs_extract
    
    return extract

def manual_epoching(data, parameters, info):
    
    extract = {}
    
    #Scrap parameters
    tmin=parameters['TMIN']
    tmax=parameters['TMAX']
    ptp_threshold=parameters['PTP_THRESHOLD']
    reject_flat=parameters['REJECT_FLAT']
    main_path=parameters['MAIN_PATH']
    add_df=parameters['ADD_DF']
    timings_dict = parameters['TIMINGS_DICT'][info['rec']]
    
    events, event_id = mne.events_from_annotations(data)

    epochs = mne.Epochs(
        data, 
        events, 
        event_id, 
        tmin = tmin, 
        tmax = tmax,
        event_repeated='drop',
        reject=dict(eeg=ptp_threshold) if ptp_threshold != None else None,
        flat=dict(eeg=1e-6) if reject_flat == True else None,
        preload = True
        )
    
    if isinstance(timings_dict, dict):
        pass
    else :
        timings_dict = get_timings_dict(data)
    
    if add_df == True :
        epochs.metadata = pd.read_csv(f'{main_path}/DATA/{info['rec'].replace('_eeg.fif', '_behav.csv')}', index_col=[0]).reset_index(drop=True)
    
    for label_name, interval in timings_dict.items():
        
        selected_epochs = epochs[int(interval[0]):int(interval[1])+1].copy()
        # RESET INDEX
        extract[f'epochs_{label_name}'] = {'no_cleaning':{'no_analysis' : {'data' : selected_epochs.copy()}}}
    
    return extract

def get_RS_crops(data, parameters, info):
    
    extract = {}
    
    if len(data.annotations.onset[data.annotations.description == 'RS']) == 2 :
        
        RS1_data_copy = copy.deepcopy(data)
        RS1_crop = RS1_data_copy.crop(tmax = data.annotations.onset[data.annotations.description == 'RS'][0])
        extract[f'raw_RS1'] = {'no_cleaning':{'no_analysis' : {'data' : RS1_crop}}}
        
        RS2_data_copy = copy.deepcopy(data)
        RS2_crop = RS2_data_copy.crop(tmin = data.annotations.onset[data.annotations.description == 'RS'][1])
        extract[f'raw_RS2'] = {'no_cleaning':{'no_analysis' : {'data' : RS2_crop}}}
    
    else :
        pass
    
    return extract


## Side functions

def display_annotations(data):

    total_annotations = len(data.annotations)

    # Display first 20 annotations
    print("First 20 Annotations:")
    for idx, annot in enumerate(zip(data.annotations.onset, data.annotations.description)):
        if idx < 150:
            print(f"Index: {idx}, Onset: {annot[0]}, Description: {annot[1]}")
        else:
            break
    
    # Display last 20 annotations
    print("Last 20 Annotations:")
    if total_annotations > 40:
        start_index = total_annotations - 40
    else:
        start_index = 0
    
    for idx in range(start_index, total_annotations):
        annot = (data.annotations.onset[idx], data.annotations.description[idx])
        print(f"Index: {idx}, Onset: {annot[0]}, Description: {annot[1]}")

def get_timings_dict(data):
    
    print('Write down start, end and name of segments')

    display_annotations(data)

    #data.plot(block=True)
    
    start_list = []
    end_list = []
    name_list = []

    while True:
        start = input("Enter the start time or indice of the interval (or 'q' to quit): ")
        if start.lower() == 'q':
            print('q')
            break
        start_list.append(start)
        end_list.append(input("Enter the end time or indice of the interval : "))
        name_list.append(input("Enter the name of the interval : "))
    
    print('end of loop')
    
    timings_dict = {name : [] for name in name_list}
    for i, name in enumerate(timings_dict):
        timings_dict[name].append(start_list[i])
        timings_dict[name].append(end_list[i])
    
    return timings_dict


