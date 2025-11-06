# Packages

import mne
import numpy as np

#import _B_Extract as _B_

from autoreject import AutoReject

from meegkit.asr import ASR
from meegkit.utils.matrix import sliding_window
from meegkit.dss import dss0, dss1
from meegkit.utils import demean, normcol, tscov, fold, rms, unfold

import copy



# Modules

def apply_ASR(data, parameters, info, original_data):
    
    clean = {}
    
    #Scrap parameters
    cutoff_list = parameters['CUTOFF']
    wl_list = parameters['WL']
    training_raw_path = parameters['TRAINING_RAW_DICT'][info['rec']]
    labels = parameters['LABELS']
    
    for cutoff in cutoff_list:
        for wl in wl_list:
            if isinstance(data, mne.io.Raw) :
                raw_to_apply_ASR = data
            elif isinstance(data, mne.Epochs) :
                raw_to_apply_ASR = original_data
            else:
                # Handle unexpected data types
                raise TypeError(f"Unsupported data type for ASR: {type(data)}")

            #Define data
            raw_data = raw_to_apply_ASR.get_data()
            print(f'raw shape : {raw_data.shape}')
            
            #Define training data
            training_raw = mne.io.read_raw(training_raw_path, preload = True)
            training_data = training_raw.get_data()

            #Define ASR
            asr = ASR(cutoff=cutoff, win_len=wl, method="euclid")
            _, sample_mask = asr.fit(training_data)

            #Define window
            sfreq = data.info['sfreq']
            X = sliding_window(raw_data, window=int(sfreq*wl), step=int(sfreq*wl))
            Y = np.zeros_like(X)

            #Apply ASR
            for i in range(X.shape[1]):
                try:
                    Y[:, i, :] = asr.transform(X[:, i, :])
                except Exception as e:
                    print(f"Error at window {i}: {e}")
                    Y[:, i, :] = X[:, i, :]  # Leave the data unchanged

            #for i in range(X.shape[1]):
            #    Y[:, i, :] = asr.transform(X[:, i, :])
            
            #Re-organize data
            clean_run = Y.reshape(raw_data.shape[0], -1)  # ensure the shape is correct
            print(f'ASR shape : {clean_run.shape}')
            cleaned_raw = mne.io.RawArray(clean_run, data.info)
            cleaned_raw.set_annotations(data.annotations)
            
            if isinstance(data, mne.io.Raw) :
                cleaned_data = cleaned_raw
            elif isinstance(data, mne.Epochs) :
                info_copy = info.copy()
                label_name = info_copy.pop('extract').replace('epochs_', '')
                parameters = {'TMIN':data.tmin,
                              'TMAX':data.tmax,
                              'PTP_THRESHOLD':None,
                              'REJECT_FLAT':False,
                              'ADD_DF': True,
                              'LABELS': {label_name : labels[label_name]}}
                cleaned_data_dict = _B_.subset_epoching(cleaned_raw, parameters, info = info_copy)
                cleaned_data = cleaned_data_dict[f'epochs_{label_name}']['no_cleaning']['no_analysis']['data']

            key = f'met-asr_cutoff-{cutoff}_wl-{wl}'
            clean[key] = {'no_analysis': {'data' : cleaned_data}}
    
    return clean

def apply_AUTOREJECT(data, parameters, info, original_data):
    
    clean = {}
    
    #Scrap parameters
    n_interpolates_list = parameters['N_INTERPOLATES']
    consensus_percs_list = parameters['CONSENSUS_PERCS']
    
    for n_interpolates in n_interpolates_list:
        for consensus_percs in consensus_percs_list:
            
            epochs = copy.deepcopy(data)

            n_samples = len(epochs)
            n_splits = min(n_samples, 10) 
            
            ar = AutoReject(
                n_interpolates, 
                consensus_percs,
                cv = n_splits,
                thresh_method='bayesian_optimization', 
                random_state=42
            )
            ar.fit(epochs.copy().filter(1, None))
            ar_epochs, reject_log = ar.transform(
                epochs.copy(), return_log=True
            )
            
            key = f'met-autoreject_nint-{n_interpolates}_cpercs-{consensus_percs}'
            clean[key] = {'no_analysis': {'data' : ar_epochs}}

    return clean

def apply_DSS(data, parameters, info, original_data):

    clean = {}
    
    #Scrap parameters
    DSS_n_components_list = parameters['DSS_N_COMPONENTS']
    DSS_threshold_list = parameters['DSS_THRESHOLD']
    
    for DSS_n_components in DSS_n_components_list:
        for DSS_threshold in DSS_threshold_list:
            epochs = copy.deepcopy(data)
        
            # Extract the data from the epochs
            data = epochs.get_data()  # shape is (n_epochs, n_channels, n_times)

            # Transpose data to (n_times, n_channels, n_epochs)
            data = np.transpose(data, (2, 1, 0))

            # Apply DSS with parameters adjusted
            todss, fromdss, pwr0, pwr1 = dss1(data, keep1=DSS_n_components, keep2=DSS_threshold)
            
            # Transform data to DSS components
            epoch_size = data.shape[0]
            z = fold(np.dot(unfold(data), todss), epoch_size=epoch_size)

            # Transform back from DSS components to sensor space
            denoised_data = fold(np.dot(unfold(z), fromdss), epoch_size=epoch_size)

            # Transpose back to original shape (n_epochs, n_channels, n_times)
            denoised_data = np.transpose(denoised_data, (2, 1, 0))

            # Update the epochs data with denoised data
            epochs._data = denoised_data
            
            
            key = f'met-dss_dssncomp-{DSS_n_components}_dssthr-{DSS_threshold}'
            clean[key] = {'no_analysis': {'data' : epochs}}


    return clean

def ptp_threshold_to_epochs(data, parameters, info, original_data):
    
    clean = {}
    
    #Scrap parameters
    reject_ptp_threshold_list = parameters['REJECT_PTP_THRESHOLD_LIST']
    flat_ptp_threshold_list = parameters['FLAT_PTP_THRESHOLD_LIST']
    
    for reject_ptp_threshold in reject_ptp_threshold_list:
        for flat_ptp_threshold in flat_ptp_threshold_list:
            
            epochs = copy.deepcopy(data)
            epochs.drop_bad(reject = dict(eeg=reject_ptp_threshold),
                            flat = dict(eeg=flat_ptp_threshold))
            
            key = f'met-ptpthreshold_reject-{reject_ptp_threshold}_flat-{flat_ptp_threshold}'
            clean[key] = {'no_analysis': {'data' : epochs}}
    
    return clean


## Combinations

def apply_ASR_and_ptp_threshold_to_epochs(data, parameters, info, original_data):
    
    clean = {}
    
    ASR_dict = apply_ASR(data, parameters['apply_ASR'], info, original_data)
    
    for ASR_key in ASR_dict.keys():
        
        ASR_data = ASR_dict[ASR_key]['no_analysis']['data']
        PTP_threshold_dict = ptp_threshold_to_epochs(ASR_data, parameters['ptp_threshold_to_epochs'], info, original_data)
        
        for PTP_threshold_key in PTP_threshold_dict.keys():
            PTP_threshold_data = PTP_threshold_dict[PTP_threshold_key]['no_analysis']['data']
            
            key = f'{ASR_key}_and_{PTP_threshold_key}'
            clean[key] = {'no_analysis': {'data' : PTP_threshold_data}}
    
    return clean


def apply_ASR_and_apply_AUTOREJECT_to_epochs(data, parameters, info, original_data):
    
    clean = {}
    
    ASR_dict = apply_ASR(data, parameters['apply_ASR'], info, original_data)
    
    for ASR_key in ASR_dict.keys():
        
        ASR_data = ASR_dict[ASR_key]['no_analysis']['data']
        AUTOREJECT_dict = apply_AUTOREJECT(ASR_data, parameters['apply_AUTOREJECT'], info, original_data)
        
        for AUTOREJECT_key in AUTOREJECT_dict.keys():
            AUTOREJECT_data = AUTOREJECT_dict[AUTOREJECT_key]['no_analysis']['data']
            
            key = f'{ASR_key}_and_{AUTOREJECT_key}'
            clean[key] = {'no_analysis': {'data' : AUTOREJECT_data}}
    
    return clean


# Dictionary
cleaning_modules_dict = {'apply_ASR' : apply_ASR,
                         'apply_AUTOREJECT' : apply_AUTOREJECT,
                         'apply_DSS' : apply_DSS,
                         'ptp_threshold_to_epochs' : ptp_threshold_to_epochs}


def cleaning_combination(data, parameters, info, original_data):
    
    data = copy.deepcopy(data)
    
    #Scrap methods from parameters
    
    modules = ['apply_ASR','apply_AUTOREJECT']
    
    #Combination
    
    clean = {}
    
    for i, module in enumerate(modules):
        module_dict = cleaning_modules_dict[module](data, parameters[module], info, original_data)
        for module_dict_key in module_dict.keys():
            data 
        
        
        
    ASR_dict = apply_ASR(data, parameters['apply_ASR'], info, original_data)
    for ASR_key in ASR_dict.keys():
        ASR_data = ASR_dict[ASR_key]['no_analysis']['data']
        
        AUTOREJECT_dict = apply_AUTOREJECT(ASR_data, parameters['apply_AUTOREJECT'], info, original_data)
        for AUTOREJECT_key in AUTOREJECT_dict.keys():
            AUTOREJECT_data = AUTOREJECT_dict[AUTOREJECT_key]['no_analysis']['data']
            
            
            key = f'{ASR_key}_and_{AUTOREJECT_key}'
            clean[key] = {'no_analysis': {'data' : AUTOREJECT_data}}
    
    return clean


## Side functions

def define_ASR_training_raw(data):

    #Define clean intervals
    print('Write down the clean intervals')

    _B_.display_annotations(data)

    data.plot(block=True)
    intervals = []
    while True:
        start = input("Enter the start time of the clean interval (in seconds, or 'q' to quit): ")
        if start.lower() == 'q':
            break
        end = input("Enter the end time of the clean interval (in seconds): ")
        intervals.append((float(start), float(end)))
    
    #Concatenate clean intervals
    clean_data = []
    for start, end in intervals:
        start_sample = int(start * data.info['sfreq'])
        end_sample = int(end * data.info['sfreq'])
        clean_data.append(data[:, start_sample:end_sample][0])
    training_raw = mne.concatenate_raws([mne.io.RawArray(data, data.info) for data in clean_data])
    return training_raw




