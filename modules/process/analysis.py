import numpy as np
import pandas as pd
import yasa
from . import cpp_process


def PSD(data, info, plot=True):
    psd_data = data.compute_psd()
    if plot == False:
        return {"psd_data": psd_data}
    psd_plot = psd_data.plot()
    return {"psd_data": psd_data, "psd_plot": psd_plot}


def spectrogram(data, info, channel, win_sec=30):
    ch_index = data.info["ch_names"].index(channel)
    data_ch = data._data[ch_index]
    spectro = yasa.plot_spectrogram(
        data=data_ch, sf=data.info["sfreq"], win_sec=win_sec
    )
    return spectro
