import modules
from parameters import PATH_LIST, PARAMETERS

import glob
import copy
import warnings
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import time
import queue


def main(path_list, parameters, apply_multiprocessing=False):
    if apply_multiprocessing:
        preprocessing_dict = preprocessing_mp(path_list, parameters)
        processing_dict = processing_mp(preprocessing_dict, parameters)
        postprocessing_dict = postprocessing(processing_dict, parameters)
    else:
        preprocessing_dict = preprocessing(path_list, parameters)
        processing_dict = processing(preprocessing_dict, parameters)
        postprocessing_dict = postprocessing(processing_dict, parameters)
    return preprocessing_dict, processing_dict, postprocessing_dict


# ----- PREPROCESSING STEP -----


def preprocessing(path_list, parameters):

    preprocessing_dict = {}

    for path in path_list:
        functions = get_functions_with_args(
            path,
            parameters=parameters["preprocessing"],
            step="preprocessing",
            step_module=modules.preprocess,
        )

        # In the preprocessing step there is only one preprocessing function allowed by file so we take only the first item.
        function, kwargs = functions[0]

        preprocessed_data = function(path, **kwargs)

        if isinstance(preprocessed_data, dict):
            preprocessing_dict.update(preprocessed_data)
        else:
            preprocessing_dict[path] = preprocessed_data

    return preprocessing_dict


def preprocessing_mp(path_list, parameters):

    preprocessing_dict = {}

    preprocess_mp_args = {"path": [], "function": [], "kwargs": []}

    for path in path_list:
        functions = get_functions_with_args(
            path,
            parameters=parameters["preprocessing"],
            step="preprocessing",
            step_module=modules.preprocess,
        )

        # In the preprocessing step there is only one preprocessing function allowed by file so we take only the first item.
        function, kwargs = functions[0]

        preprocess_mp_args["path"].append(path)
        preprocess_mp_args["function"].append(function)
        preprocess_mp_args["kwargs"].append(kwargs)

    with ProcessPoolExecutor() as executor:
        for path, preprocessed_data in executor.map(
            preprocess_mp,
            preprocess_mp_args["path"],
            preprocess_mp_args["function"],
            preprocess_mp_args["kwargs"],
        ):
            if isinstance(preprocessed_data, dict):
                preprocessing_dict.update(preprocessed_data)
            else:
                preprocessing_dict[path] = preprocessed_data

    return preprocessing_dict


def preprocess_mp(path, function, kwargs):
    preprocessed_data = function(path, **kwargs)
    return path, preprocessed_data


# ----- PROCESSING STEP -----


def processing(preprocessing_dict, parameters):

    initial_processing_dict = preprocessing_dict_to_initial_processing_dict(
        preprocessing_dict, parameters
    )
    processing_dict = {}

    for file_path, empty_tree in initial_processing_dict.items():
        individual_dict = rec_processing(
            individual_dict={file_path: empty_tree},
            parameters=parameters,
            steps=list(parameters["processing"].keys()),
        )
        processing_dict.update(individual_dict)

    return processing_dict


def processing_mp(preprocessing_dict, parameters):

    initial_processing_dict = preprocessing_dict_to_initial_processing_dict(
        preprocessing_dict, parameters
    )
    processing_dict = {}

    process_mp_args = {
        "file_path": list(initial_processing_dict.keys()),
        "empty_tree": list(initial_processing_dict.values()),
        "parameters": [parameters] * len(list(initial_processing_dict.keys())),
    }

    with ProcessPoolExecutor() as executor:
        for individual_dict in executor.map(
            process_mp, process_mp_args["file_path"], process_mp_args["empty_tree"]
        ):
            processing_dict.update(individual_dict)

    return processing_dict


def process_mp(file_path, empty_tree, parameters=PARAMETERS):
    individual_dict = rec_processing(
        individual_dict={file_path: empty_tree},
        parameters=parameters,
        steps=list(parameters["processing"].keys()),
    )
    return individual_dict


def preprocessing_dict_to_initial_processing_dict(preprocessing_dict, parameters):
    initial_processing_dict = {}
    for file_path, data in preprocessing_dict.items():
        initial_processing_dict[file_path] = nest_data(
            list(parameters["processing"].keys()), data
        )  # Put the preprocessed data at the bottom of the nested processing dict.
    return initial_processing_dict


def rec_processing(individual_dict, parameters, steps, nstep=0, info={}):

    if len(steps) == 0:
        return individual_dict

    if nstep >= len(steps):
        return individual_dict

    sub_step = steps[nstep]

    for key in individual_dict.keys():

        if nstep == 0:
            info["file_name"] = key
        else:
            info[steps[nstep - 1]] = key

        functions = get_functions_with_args(
            info=info,
            parameters=parameters["processing"][sub_step],
            step="processing",
            step_module=getattr(modules, sub_step),
        )

        initial_data = unnest_data(
            individual_dict[key]
        )  # Unnest the preprocessed data from the bottom of the dict.

        for f in functions:

            function, kwargs = f
            processed_data = function(
                data=copy.deepcopy(initial_data), info=info, **kwargs
            )

            if isinstance(processed_data, dict):
                for label, ind_data in processed_data.items():
                    individual_dict[key].update(
                        {label: nest_data(steps=steps[nstep + 1 :], data=ind_data)}
                    )  # Put the processed data at the bottom of the nested dict.
            else:
                individual_dict[key][function.__name__] = nest_data(
                    steps=steps[nstep + 1 :], data=processed_data
                )  # Put the processed data at the bottom of the nested dict.

        rec_processing(
            individual_dict[key], parameters, steps, nstep=nstep + 1, info=info
        )

    return individual_dict


# ----- POSTPROCESSING STEP -----


def postprocessing(processing_dict, parameters):

    postprocessing_dict = {}

    if not 'postprocessing' in parameters.keys():
        return {}

    functions = get_functions_with_args(
        info=None,
        parameters=parameters["postprocessing"],
        step="postprocessing",
        step_module=modules.postprocess,
    )

    for f in functions:
        function, kwargs = f
        data = function(processing_dict, parameters, **kwargs)
        postprocessing_dict[function.__name__] = data

    return postprocessing_dict


def postprocessing_mp(processing_dict, parameters):

    postprocessing_dict = {}

    if not 'postprocessing' in parameters.keys():
        return {}

    functions = get_functions_with_args(
        info=None,
        parameters=parameters["postprocessing"],
        step="postprocessing",
        step_module=modules.postprocess,
    )

    postprocess_mp_args = {"function": [], "kwargs": [], "processing_dict": []}

    for f in functions:
        function, kwargs = f
        postprocess_mp_args["function"].append(function)
        postprocess_mp_args["kwargs"].append(kwargs)
        postprocess_mp_args["processing_dict"].append(processing_dict)

    with ProcessPoolExecutor() as executor:
        for function, data in executor.map(
            postprocess_mp,
            postprocess_mp_args["function"],
            postprocess_mp_args["kwargs"],
            postprocess_mp_args["processing_dict"],
        ):
            postprocessing_dict[function.__name__] = data

    return postprocessing_dict


def postprocess_mp(function, kwargs, processing_dict, parameters=PARAMETERS):
    data = function(processing_dict, parameters, **kwargs)
    return function, data


# ----- HELPER FUNCTIONS -----


def get_functions_with_args(info, parameters, step, step_module):

    functions = []

    if step == "postprocessing":
        for function_name, kwargs in parameters.items():
            function = getattr(step_module, function_name)
            functions.append((function, kwargs))
        return functions

    options = [
        opt["FUNCTIONS"] for opt in parameters.values() if opt["CONDITION"](info)
    ]

    if (
        len(options) == 0
    ):  # We don't permit to ignore any file of the query on the preprocessing step, but it's not a problem for the processing step.
        if step == "preprocessing":
            raise Exception(f"No conditions matching for {info}.")
        elif step == "processing":
            warnings.warn(f"No conditions matching for {info}.")
            return []

    elif len(options) > 1:
        raise Exception(
            f"Conditions should be mutually exclusive. {len(option)} conditions matched for {info}."
        )

    else:
        option = options[0]

    for function_name, kwargs in option.items():
        function = getattr(step_module, function_name)
        functions.append((function, kwargs))

    return functions


def nest_data(steps, data):
    if len(steps) == 0:
        return data
    if len(steps) == 1:
        return {f"no_{steps[0]}": data}
    return {f"no_{steps[0]}": nest_data(steps[1:], data)}


def unnest_data(d):
    if len(d.keys()) > 1:
        raise Exception("There shouldn't be more than one key at this step.")
    value = d[list(d.keys())[0]]
    if isinstance(value, dict):
        return unnest_data(value)
    return value


if __name__ == "__main__":

    start = time.perf_counter()
    preprocessing_dict, processing_dict, postprocessing_dict = main(
        path_list=PATH_LIST,
        parameters=PARAMETERS,
        apply_multiprocessing=False,
    )
    end = time.perf_counter()

    print(f"PREPROCESSING DICT : {preprocessing_dict}")
    print(f"PROCESSING DICT : {processing_dict}")
    print(f"POSTPROCESSING DICT : {postprocessing_dict}")

    print(f"duration : {end-start}")
