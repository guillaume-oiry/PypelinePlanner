import mne
from . import cpp_process


def raw_eeg_to_fixed_length_epochs(data, info, duration=30, cpp_acceleration=False):
    if cpp_acceleration:
        epochs_data = cpp_process.cut_raw_data_to_epochs(data=data._data, duration=duration, sfreq=int(data.info["sfreq"]))
        epochs = mne.EpochsArray(epochs_data, info=data.info)
        return {f"epochs_{duration}": epochs}
    epochs = mne.make_fixed_length_epochs(data, duration=duration, preload=True)
    return {f"epochs_{duration}": epochs}

