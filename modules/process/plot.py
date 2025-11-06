# Packages

import numpy as np
import yasa

import matplotlib.pyplot as plt

import copy


# Modules

def plot_epochs_single_channel(data, parameters, info):
    
    plot = {}
    
    #Scrap parameters
    ch_name_list = parameters['CH_NAME']
    
    for ch_name in ch_name_list :
        
        epochs = copy.deepcopy(data)
        epochs_data = epochs.get_data(picks=ch_name) * 1e6
        n_epochs = epochs_data.shape[0]
        times = epochs.times
        
        fig, ax1 = plt.subplots(1, 1, figsize=(14, 6))
        for epoch in range(n_epochs):
            ax1.plot(times, epochs_data[epoch, :][0], alpha=1)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude (µV)')
        ax1.set_title(f'{ch_name}')
        ax1.legend().set_visible(False)
        ax1.get_yaxis().get_major_formatter().set_useOffset(False)
        ax1.get_yaxis().get_major_formatter().set_scientific(False)
        plt.tight_layout()
        plt.close()
        
        plot[f'all_epochs_{ch_name}'] = fig
    
    return plot

def PSD_plot(data, parameters, info):
    
    plot = {}

    ch = ['Fp1','Fp2','Fz','Cz','Pz','O1','O2']
    
    data = np.log10(data)

    ndim = data.ndim
    if ndim == 3:
        data_std = np.std(data, axis=0)
        data = np.mean(data, axis=0)
    
    fig, ax = plt.subplots(
        nrows=1, ncols=1, figsize=(12, 12), layout = "constrained")
    
    freqs = np.linspace(0.5, 40, 80)
    for i in range(data.shape[0]):
        ax.plot(freqs, np.array(data[i]).T, label = ch[i], alpha = .8)
        if ndim == 3 :
            ax.fill_between(freqs, data[i] - data_std[i], data[i] + data_std[i], alpha = .1)
    
    # Set the title and labels
    ax.set_title(f'PSD', fontsize=50)
    ax.set_xlabel('Frequency (Hz)', fontsize=30)
    ax.set_ylabel('(dB)', fontsize=30) # this is dB
    ax.set_xlim([0.5, 40])
    
    # ax.set_ylim([-30, 60])
    ax.legend()
    
    # Show the plot
    plt.legend(prop={'size':40})
    plt.close()
    
    plot['PSD_plot'] = fig
    
    return plot

def ERP_plot(data, parameters, info):
    
    plot = {}
    
    fig = data.plot(show=False)
    
    plot['ERP_plot'] = fig
    
    return plot

def spectrogram(data, parameters, info):
    
    plot = {}
    
    for pick in parameters['CH_PICK'] :
        raw_data = data.get_data(picks=pick)
        fig = yasa.plot_spectrogram(raw_data[0], sf = data.info['sfreq'], fmin = 0.5, fmax = 40, trimperc = 10)
        plot[f'raw_{pick}_spectrogram3_plot'] = fig
    
    return plot


