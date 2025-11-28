import mne
from . import cpp_process


def raw_eeg_to_fixed_length_epochs(data, info, duration=30):
    epochs = mne.make_fixed_length_epochs(data, duration=duration, preload=True)
    return {f"epochs_{duration}": epochs}
