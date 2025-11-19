DATA_QUERY = "DATA/*.fif"

preprocessing_parameters = {
    "all": {
        "CONDITION": lambda file_path: "task-sart" in file_path,
        "PARAMETERS": {
            "EPICE_minimal_preprocessing": {
                "LOW_FREQ": 0.1,
                "HIGH_FREQ": 40,
                "NOTCH_FILTER": 50,
            }
        },
    },
    "other": {
        "CONDITION": lambda file_path: "task-sart" not in file_path,
        "PARAMETERS": {
            "EPICE_minimal_preprocessing": {
                "LOW_FREQ": 0.1,
                "HIGH_FREQ": 40,
                "NOTCH_FILTER": 50,
            }
        },
    },
}

processing_parameters = {
    "extraction": {
        "all": {
            "CONDITION": lambda info: True,
            "PARAMETERS": {
                "subset_epoching": {
                    "tmin": -20,
                    "tmax": 0,
                    "ptp_threshold": None,
                    "reject_flat": 1e-6,
                    "add_df": False,
                    "labels": {"probe": "probe"},
                }
            },
        }
    },
    "analysis": {
        "epochs": {
            "CONDITION": lambda info: "epochs" in info["extraction"],
            "PARAMETERS": {"psd_data": {"bp": False}},
        }
    },
}

postprocesssing_parameters = {"psd_mean": {}, "psd_mean": {}, "psd_mean": {}}

PARAMETERS = {
    "preprocessing": preprocessing_parameters,
    "processing": processing_parameters,
    "postprocessing": postprocesssing_parameters,
}
