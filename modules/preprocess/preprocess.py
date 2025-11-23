import mne
import pandas as pd


# Modules
def EEG_minimal_filtering(path, l_freq=0.1, h_freq=40, notch_f=50):
    raw = mne.io.read_raw(path, preload=True)
    raw.filter(l_freq, h_freq)
    raw.notch_filter(notch_f)
    return raw


def load_tsv(path):
    df = pd.read_table(path)
    return {"participants_info": df}
