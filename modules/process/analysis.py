# Packages

import numpy as np
import pandas as pd
from scipy.stats import exponnorm

import copy


# Constants

location_dict = {'Fp1' : 'Frontal',
                 'Fp2' : 'Frontal',
                 'Fz' : 'Frontal',
                 'Cz' : 'Central',
                 'Pz' : 'Central',
                 'O1' : 'Posterior',
                 'O2' : 'Posterior',
                 'Fpz' : 'Frontal',
                 'Oz' : 'Occipital'}


# Modules

def PSD_data(data, info, bp):
    
    analysis = {}
    
    # Check data type
    if 'Raw' in str(type(data)) :
        data_type = 'raw'
    elif 'Epochs' in str(type(data)) :
        data_type = 'epochs'
    else :
        raise TypeError('Only raws and epochs are allowed.')
    
    psd = data.compute_psd(
        method = 'welch',
        fmin = 0.5, 
        fmax = 40,
        n_fft = 500,
        n_overlap = 250,
        n_per_seg = 500,
        window = 'hamming',
        )
    
    psd_data = psd.get_data()

    analysis[f'PSD'] = {'data': psd_data}
    '''
    if bp :
        analysis[f'BP'] = {'data': BP_data(psd_data)}
    '''

    return analysis

def Spectrum(data, parameters, info):
    
    #Scrap parameters
    bp = parameters['BP']

    #Core
    psd = data.compute_psd(
            method = 'welch',
            fmin = 0.5, 
            fmax = 40,
            n_fft = 500,
            n_overlap = 250,
            n_per_seg = 500,
            window = 'hamming',
            )

    df = pd.DataFrame()

    def add_psd_segment_to_df(df, psd, is_epochs = False, n_epoch = None):

        for ch in psd.info['ch_names']:

            try :
                values = psd.copy().pick(ch).get_data().flatten()
            except :
                values = np.nan
            
            series_list = [pd.Series(data = values,
                                     index = pd.MultiIndex.from_arrays([np.full(len(psd.freqs),'PSD'), psd.freqs])),
                           pd.Series(data = info.values(),
                                     index = pd.MultiIndex.from_arrays([np.full(len(info),'infos'), info.keys()])),
                           pd.Series(data = [ch],
                                     index = pd.MultiIndex.from_arrays([['infos'], ['ch']]))]
            
            if is_epochs :
                series_list.append(pd.Series(data = [n_epoch],
                                             index = pd.MultiIndex.from_arrays([['infos'], ['n_epoch']])))
                series_list.append(pd.Series(data = psd.metadata.squeeze().values,
                                             index = pd.MultiIndex.from_arrays([np.full(len(psd.metadata.squeeze().index),'behav'), psd.metadata.squeeze().index])))
            
            line = pd.concat(series_list)
            
            df = pd.concat([df, pd.DataFrame([line])], ignore_index = True)

        return df
    
    if 'Raw' in str(type(data)) :
        df = add_psd_segment_to_df(df, psd)
    elif 'Epochs' in str(type(data)) :
        for n, epoch_psd in enumerate(psd) :
            df = add_psd_segment_to_df(df, psd[n], is_epochs = True, n_epoch = n)
    else :
        raise TypeError('Only raws and epochs are allowed.')

    if bp :
        
        df[('BP', 'total_power')] = np.trapz(df.PSD, x = df.PSD.columns)
        for band_name, interval in bp.items():
            idx_band = df.PSD.columns[(interval[0] <= df.PSD.columns) & (df.PSD.columns < interval[1])]
            df[('BP', f'abs_{band_name}')] = np.trapz(df.PSD[idx_band], x = idx_band)
            df[('BP', f'rel_{band_name}')] = df[('BP', f'abs_{band_name}')] / df[('BP', 'total_power')]
        df = df.drop(('BP','total_power'), axis=1)

    #Wrap up
    analysis = {'Spectrum' : {'data' : df}}

    return analysis

def ERP_data(data, parameters, info):
    
    analysis = {}
    
    data_copy = copy.deepcopy(data)
    
    evoked = data_copy.average()
    
    analysis[f'ERP'] = {'data': evoked}

    return analysis


def SW_detect(data, parameters, info) :
    
    analysis = {}
    
    # Scrap parameters
    get_SW = parameters['GET_SW']
    filter_range = parameters['FILTER_RANGE']
    threshold = parameters['THRESHOLD']
    new_sfreq = parameters['NEW_SFREQ']
    location_dict = parameters['LOCATION_DICT']

    # Check data type
    if 'Raw' in str(type(data)) :
        data_type = 'raw'
        sample = 1
    elif 'Epochs' in str(type(data)) :
        data_type = 'epochs'
        sample = len(data)
    else :
        raise TypeError('Only raws and epochs are allowed.')
    
    # Get info
    sfreq = data.info['sfreq']
    n_epochs, nchan, nsamples = data.get_data().shape
    bads = [data.ch_names.index(bad) for bad in data.info['bads']]
    
    # Preprocessing
    data = copy.deepcopy(data)
    data.filter(
        filter_range[0], filter_range[1], 
        l_trans_bandwidth='auto', h_trans_bandwidth='auto',
        filter_length='auto', phase='zero'
        )
    data.resample(new_sfreq, npad='auto')
    
    df = pd.DataFrame()
    
    for n in range(sample) :
        
        for ch, ch_name in enumerate(data.info['ch_names']):
            
            if ch in bads :
                print(f'Ignoring : {data.info['ch_names'][ch]} (bad channel)')
                continue
            
            print(f'Processing: {data.info['ch_names'][ch]}')
            
            signal = data[n].pick(ch_name).copy().get_data(units = 'uV').flatten()
    
            # Detection of slow waves

            ## Find 0-crossings
            zero_crossing = (signal > 0).astype(int)
            
            ## Find positive (start of potential SW) and negative (end of potential SW) zero-crossing 
            pos_crossing_idx = np.where(np.diff(zero_crossing) > 0)[0] + 1
            neg_crossing_idx = np.where(np.diff(zero_crossing) < 0)[0] + 1
            if neg_crossing_idx[0] >= pos_crossing_idx[0]:
                pos_crossing_idx = pos_crossing_idx[1:]
                start = 2
            else :
                start = 1
 
            ## Find peaks and troughs (Rejects peaks below zero and troughs above zero)
            derived_signal = np.convolve(np.diff(signal), np.ones((5,))/5, mode='valid')
            threshold_crossing = (derived_signal > threshold).astype(int)
            difference = np.diff(threshold_crossing)
            
            peaks = np.where(difference == -1)[0] + 1 #not the index just before ?
            peaks = peaks[signal[peaks] > 0]
            
            troughs = np.where(difference == 1)[0] + 1
            troughs = troughs[signal[troughs] < 0] #risk of having two peaks that follow each other ?
            
            lastpk = np.nan

            for wndx in range(start,len(neg_crossing_idx) - 1):
                
                if pos_crossing_idx[wndx] > len(derived_signal):
                    continue
                
                wavest = neg_crossing_idx[wndx]
                wavend = neg_crossing_idx[wndx + 1]
            
                tp1t = np.where(troughs>wavest)
                tp2t = np.where(troughs<wavend)
                negpeaks = troughs[np.intersect1d(tp1t,tp2t)]
                ## In case a peak is not detected for this wave (happens rarely)
                if np.size(negpeaks) == 0:
                    #waves[wndx, :] = np.nan
                    continue
            
                tp1p = np.where(peaks > wavest)
                tp2p = np.where(peaks <= wavend)
                pospeaks = peaks[np.intersect1d(tp1p,tp2p)]
                # if negpeaks is empty set negpeak to pos ZX
                if np.size(pospeaks) == 0 :
                    pospeaks = np.append(pospeaks,wavend)
            
                b = [np.min(signal[negpeaks])][0]
                c = [np.max(signal[pospeaks])][0]
                cx = pospeaks[np.where(signal[pospeaks]==c)][0]
                poszx = pos_crossing_idx[wndx]
                nperiod = poszx-wavest;
    
                wave = {"session" : info['sub'],
                        "extract" : info['extract'],
                        "cleaning" : info['method'],
                        "ch_name" : data.info["ch_names"][int(ch)],
                        "location" : location_dict[data.info["ch_names"][int(ch)]],
                        "start" : wavest*(sfreq/new_sfreq), #0:  wave beginning (sample)
                        "end"  : wavend*(sfreq/new_sfreq), #1:  wave end (sample)
                        "middle" : (wavest+np.ceil(nperiod/2))*(sfreq/new_sfreq), #2:  wave middle point (sample)
                        "neg_halfway" : poszx*(sfreq/new_sfreq), #3:  wave negative half-way (sample)
                        "period" : (wavend-wavest)/new_sfreq, #4:  period in seconds
                        "neg_amp_peak" : np.abs(b), #most pos peak /abs for matrix #5:  negative amplitude peak
                        "neg_peak_pos" : (negpeaks[np.where(signal[negpeaks]==b)][0])*(sfreq/new_sfreq), #max pos peak location in entire night #6:  negative amplitude peak position (sample)
                        "pos_amp_peak" : c, #most neg peak #7:  positive amplitude peak
                        "pos_peak_pos" : cx*(sfreq/new_sfreq), #max neg peak location in entire night #8:  positive amplitude peak position (sample)
                        "PTP" : c-b, #max peak to peak amp #9:  peak-to-peak amplitude
                        "1st_negpeak_amp" : np.abs(signal[negpeaks[0]]), #1st pos peak amp #10: 1st neg peak amplitude
                        "1st_negpeak_amp_pos" : (negpeaks[0])*(sfreq/new_sfreq), #1st pos peak location #11: 1st neg peak amplitude position (sample)
                        "last_negpeak_amp" : np.abs(signal[negpeaks[len(negpeaks)-1]]), #last pos peak amp #12: Last neg peak amplitude
                        "last_negpeak_amp_pos" : (negpeaks[len(negpeaks)-1])*(sfreq/new_sfreq), #last pos peak location #13: Last neg peak amplitude position (sample)
                        "1st_pospeak_amp" : signal[pospeaks[0]], #1st neg peak amp #14: 1st pos peak amplitude
                        "1st_pospeak_amp_pos" : (pospeaks[0])*(sfreq/new_sfreq), #1st pos peak location #15: 1st pos peak amplitude position (sample)
                        "mean_amp" : np.abs(np.mean(signal[negpeaks])), #16: mean wave amplitude
                        "n_negpeaks" : len(negpeaks), #now number of positive peaks #17: number of negative peaks
                        "pos_halfway_period" : nperiod/new_sfreq, #neghalfwave period #18: wave positive half-way period
                        "1peak_to_npeak_period" : (cx-lastpk)/new_sfreq, #1st peak to last peak period #19: 1st peak to last peak period
                        "inst_neg_1st_segment_slope" : np.abs(np.min(derived_signal[wavest:pos_crossing_idx[wndx]])) * new_sfreq, #determines instantaneous positive 1st segement slope on smoothed signal, (name not representative) #20: determines instantaneous negative # 1st segement slope on smoothed signal
                        "max_pos_slope_2nd_segment" : np.max(derived_signal[wavest:pos_crossing_idx[wndx]]) * new_sfreq, #determines maximal negative slope for 2nd segement (name not representative) #21: determines maximal positive slope for 2nd segement
                        }
                if data_type == 'epochs' :
                    wave["epoch_num"] = n #22: epoch number,
                    wave["time"] = data[n].metadata.Time.values[0]
                    wave["mindstate"] = data[n].metadata.Mindstate.values[0] #24: mindstate
                    wave["confidence"] = data[n].metadata.Confidence.values[0]
                    wave["voluntary"] = data[n].metadata.Voluntary.values[0]
                    wave["sleepiness"] = data[n].metadata.Sleepiness.values[0]
                
                lastpk = cx

                new_wave = pd.DataFrame([wave])
                if df.empty:
                    df = new_wave
                else :
                    df = pd.concat([df, new_wave], ignore_index=True)

    #df = df.dropna()

    # Wrap analysis
    analysis['AW'] = {'data': df}
    
    if get_SW & df.empty == False:
        analysis['SW'] = from_all_to_slow_waves(data = df,
                                                parameters = {'PTP' : 150,
                                                              'POS_AMP_PEAK' : 75,
                                                              'SLOPE_RANGE' : [0.25, 2],
                                                              'THRESHOLD' : None},
                                                info=info)['SW']
    else :
        analysis['SW'] = {'data': df}

    return analysis

def from_all_to_slow_waves(data, parameters, info) :

    analysis = {}

    # Scrap parameters
    PTP = parameters['PTP']
    pos_amp_peak = parameters['POS_AMP_PEAK']
    slope_range = parameters['SLOPE_RANGE']
    threshold = parameters['THRESHOLD']

    # Core
    df = data.loc[
        (data['PTP'] < PTP)
        & (data['pos_amp_peak'] < pos_amp_peak)
        & (data["pos_halfway_period"] <= slope_range[1])
        & (data["pos_halfway_period"] >= slope_range[0])
        ]
    
    thresh_dic = {}    
    for i, chan in enumerate(df.dropna().ch_name.unique()):
        temp_p2p = np.asarray(df.PTP.loc[(df['ch_name'] == chan)])
        if len(temp_p2p) == 0 :
            continue
        bins = np.arange(0, temp_p2p.max(), 0.1)
        params = exponnorm.fit(temp_p2p)#, floc=temp_sw[:,9].min())
        mu, sigma, lam = params
        y = exponnorm.pdf(bins, mu, sigma, lam)
        max_gaus = bins[np.where(y == max(y))][0] * 2
        thresh_dic[chan] = max_gaus
    
    df = pd.concat(
        [df[
         (df.ch_name == chan)
         & (df.PTP > thresh_dic[chan])]
         for chan in thresh_dic.keys()
         if len(thresh_dic.keys()) > 0
        ]
    )

    # Wrap analysis
    analysis['SW'] = {'data': df}
    
    return analysis


