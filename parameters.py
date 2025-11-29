import glob

PATH_LIST = glob.glob("DATA/ds004577/sub-*/ses-*/eeg/*.edf")
PATH_LIST.append("DATA/ds004577/participants.tsv")

preprocessing_parameters = {
    "eeg": {
        "CONDITION": lambda path: ".edf" in path,
        "FUNCTIONS": {
            "EEG_minimal_filtering": {"l_freq": 0.1, "h_freq": 40, "notch_f": 60}
        },
    },
    "participants": {
        "CONDITION": lambda path: "participants.tsv" in path,
        "FUNCTIONS": {"load_tsv": {}},
    },
}

processing_parameters = {
    "extraction": {
        "eeg": {
            "CONDITION": lambda info: ".edf" in info["file_name"],
            "FUNCTIONS": {"raw_eeg_to_fixed_length_epochs": {"duration": 20}},
        }
    },
    "analysis": {
        "raw": {
            "CONDITION": lambda info: ("no_extraction" in info["extraction"])
            and (".edf" in info["file_name"]),
            "FUNCTIONS": {
                "PSD": {"plot": False},
                "spectrogram": {"channel": "FZ", "win_sec": 10},
            },
        },
        "epochs": {
            "CONDITION": lambda info: "epochs" in info["extraction"],
            "FUNCTIONS": {"PSD": {"plot": False}},
        },
    },
}

postprocessing_parameters = {"psd_mean": {"plot_freqs_interval": [0, 50]}}

PARAMETERS = {
    "preprocessing": preprocessing_parameters,
    "processing": processing_parameters,
    "postprocessing": postprocessing_parameters,
}

'''

PATH_LIST = glob.glob("tests/DATA/*.edf")

preprocessing_parameters = {
    "0-1": {
        "CONDITION": lambda path: "0.edf" in path or "1.edf" in path,
        "FUNCTIONS": {
            "EEG_minimal_filtering": {
                "l_freq": 0.1,
                "h_freq": 40,
                "notch_f": 60,
            }
        },
    },
    "2-3": {
        "CONDITION": lambda path: "2.edf" in path or "3.edf" in path,
        "FUNCTIONS": {
            "EEG_minimal_filtering": {
                "l_freq": 1,
                "h_freq": 40,
                "notch_f": 50,
            }
        },
    },
}

processing_parameters = {
    "extraction": {
        "eeg": {
            "CONDITION": lambda info: True,
            "FUNCTIONS": {"raw_eeg_to_fixed_length_epochs": {"duration": 10}},
        }
    },
    "analysis": {
        "raw": {
            "CONDITION": lambda info: ("no_extraction" in info["extraction"])
            and (".edf" in info["file_name"]),
            "FUNCTIONS": {
                "PSD": {"plot": False},
                "spectrogram": {"channel": "EEG 2", "win_sec": 2},
            },
        },
        "epochs": {
            "CONDITION": lambda info: "epochs" in info["extraction"],
            "FUNCTIONS": {"PSD": {"plot": False}},
        },
    },
}

postprocessing_parameters = {"psd_mean": {"plot_freqs_interval": [0, 50]}}

PARAMETERS = {
    "preprocessing": preprocessing_parameters,
    "processing": processing_parameters,
    "postprocessing": postprocessing_parameters,
}

'''
