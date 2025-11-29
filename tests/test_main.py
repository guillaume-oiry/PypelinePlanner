"""
Those unit tests only assure that the structure of the resulting dictionaries are ok,
not the data itself, since this depends on the specific submodules each user adds and
actually uses. Feel free to add any specific test for your data.

NOTE : As you may have noticed, the unit tests don't check for the multiprocessing
version of the pipeline, as it relies on the PARAMETERS global variable imported
directly from parameters.py in main.py (because each worker re-imports modules with
the spawn method), and we can't pass lambda functions directly to multiprocessing, as
they are not picklable. But the single-process version is fully tested.
"""

import unittest
import main

import glob


class TestPreprocess(unittest.TestCase):

    def test_main_base_case(self):
        PATH_LIST = []
        PARAMETERS = {}

        preprocessing_dict, processing_dict, postprocessing_dict = main.main(
            path_list=PATH_LIST, parameters=PARAMETERS, apply_multiprocessing=False
        )

        self.assertEqual(
            (preprocessing_dict, processing_dict, postprocessing_dict),
            ({}, {}, {}),
        )

    def test_main_single_file(self):
        PATH_LIST = ["tests/DATA/fake_eeg_data_0.edf"]

        preprocessing_parameters = {
            "eeg": {
                "CONDITION": lambda path: True,
                "FUNCTIONS": {
                    "EEG_minimal_filtering": {
                        "l_freq": 0.1,
                        "h_freq": 40,
                        "notch_f": 60,
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
                "all": {
                    "CONDITION": lambda info: True,
                    "FUNCTIONS": {
                        "PSD": {"plot": False},
                    },
                },
            },
        }

        postprocessing_parameters = {}

        PARAMETERS = {
            "preprocessing": preprocessing_parameters,
            "processing": processing_parameters,
            "postprocessing": postprocessing_parameters,
        }

        preprocessing_dict, processing_dict, postprocessing_dict = main.main(
            path_list=PATH_LIST, parameters=PARAMETERS, apply_multiprocessing=False
        )

        test_preprocessing_dict = {"tests/DATA/fake_eeg_data_0.edf": None}
        test_processing_dict = {
            "tests/DATA/fake_eeg_data_0.edf": {
                "no_extraction": {"no_analysis": None, "psd_data": None},
                "epochs_10": {"no_analysis": None, "psd_data": None},
            }
        }
        test_postprocessing_dict = {}

        self.assertEqual(
            (
                get_keys(preprocessing_dict),
                get_keys(processing_dict),
                get_keys(postprocessing_dict),
            ),
            (
                get_keys(test_preprocessing_dict),
                get_keys(test_processing_dict),
                get_keys(test_postprocessing_dict),
            ),
        )

    def test_main_multiple_files(self):
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

        preprocessing_dict, processing_dict, postprocessing_dict = main.main(
            path_list=PATH_LIST, parameters=PARAMETERS, apply_multiprocessing=False
        )

        test_preprocessing_dict = {
            "tests/DATA/fake_eeg_data_3.edf": None,
            "tests/DATA/fake_eeg_data_2.edf": None,
            "tests/DATA/fake_eeg_data_0.edf": None,
            "tests/DATA/fake_eeg_data_1.edf": None,
        }
        test_processing_dict = {
            "tests/DATA/fake_eeg_data_3.edf": {
                "no_extraction": {
                    "no_analysis": None,
                    "psd_data": None,
                    "spectrogram": None,
                },
                "epochs_10": {"no_analysis": None, "psd_data": None},
            },
            "tests/DATA/fake_eeg_data_2.edf": {
                "no_extraction": {
                    "no_analysis": None,
                    "psd_data": None,
                    "spectrogram": None,
                },
                "epochs_10": {"no_analysis": None, "psd_data": None},
            },
            "tests/DATA/fake_eeg_data_0.edf": {
                "no_extraction": {
                    "no_analysis": None,
                    "psd_data": None,
                    "spectrogram": None,
                },
                "epochs_10": {"no_analysis": None, "psd_data": None},
            },
            "tests/DATA/fake_eeg_data_1.edf": {
                "no_extraction": {
                    "no_analysis": None,
                    "psd_data": None,
                    "spectrogram": None,
                },
                "epochs_10": {"no_analysis": None, "psd_data": None},
            },
        }
        test_postprocessing_dict = {
            "psd_mean": {
                "raw": {"data": None, "plot": None},
                "epochs": {"data": None, "plot": None},
            }
        }

        self.assertEqual(
            (
                get_keys(preprocessing_dict),
                get_keys(processing_dict),
                get_keys(postprocessing_dict),
            ),
            (
                get_keys(test_preprocessing_dict),
                get_keys(test_processing_dict),
                get_keys(test_postprocessing_dict),
            ),
        )


def get_keys(d):
    klist = []
    for k, v in d.items():
        klist.append(k)
        if isinstance(v, dict):
            klist.append(get_keys(v))
    return klist
