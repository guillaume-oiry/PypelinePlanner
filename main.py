import modules
from parameters import PARAMETERS
import glob
import warnings
import copy
from multiprocessing import Process
import time


def main(file_path_list, parameters):

    def preprocessing():
        print("starting preprocessing")
        preprocessing_dict = {}
        preprocessing_options = parameters['preprocessing'].values()
        for file_path in file_path_list:
            # MP
            option = [opt['PARAMETERS'] for opt in preprocessing_options if opt['CONDITION'](file_path)]
            if len(option) == 0 :
                warnings.warn(f"No conditions matching for {file_path}")
            elif len(option) > 1 :
                raise Exception(f"Conditions should be mutually exclusive. {len(option)} conditions matched for {file_path}")
            else :
                option = option[0]
            function = list(option.keys())[0]
            # need error handling here ?
            kwargs = option[function]
            preprocessing_function = getattr(modules.preprocess, function)
            raw = preprocessing_function(file_path, parameters = kwargs, info=file_path)
            preprocessing_dict[file_path[5:]] = nest_data(list(parameters['processing'].keys()), raw) #not pretty the removal of 'DATA'
        return preprocessing_dict

    def processing(main_dict, steps = list(parameters['processing'].keys()), nstep = 0, info = {}):

        print("starting processing")

        if len(steps) == 0:
            return main_dict

        if nstep >= len(steps):
            return main_dict

        step = steps[nstep]
        step_module = getattr(modules, step)
        processing_step_options = parameters['processing'][step]
        for key in main_dict.keys():
            # MP
            if nstep == 0:
                info['file_name'] = key
            else:
                info[steps[nstep-1]] = key
            option = [opt['PARAMETERS'] for opt in processing_step_options.values() if opt['CONDITIONS'](info)]
            if len(option) == 0 :
                warnings.warn(f"No conditions matching for {key}")
                continue
            elif len(option) > 1 :
                raise Exception(f"Conditions should be mutually exclusive. {len(option)} conditions matched for {key}")
            else :
                option = option[0]
            for function, kwargs in option.items():
                step_function = getattr(step_module, function)
                datas = step_function(unnest_data(main_dict[key]), info, **kwargs) # returned data should be a dict with {label : data, [...]}
                for label, data in datas.items():
                    main_dict[key].update({label : nest_data(steps = steps[nstep+1:], data = data)})
            processing(main_dict[key], steps, nstep = nstep+1, info = info)

    def postprocessing(processing_dict, parameters):

        print("starting postprocessing")

        postprocessing_dict = {}

        postprocessing_parameters = parameters['postprocessing']

        for function, kwargs in postprocessing_parameters.items():
            # MP
            postprocessing_function = getattr(modules.postprocessing_functions, function)
            data = postprocessing_function(copy.deepcopy(processing_dict), parameters, **kwargs) # returned data should be a dict with {label : data, [...]}
            postprocessing_dict[function] = data

        return postprocessing_dict

        '''
        def postprocessing_scheme(processing_dict, scheme_dict, scheme_steps, scheme_parameters, processing_steps = processing_steps):

            if len(scheme_steps) == 0:
                return scheme_dict

            step = scheme_steps[0]
            step_parameters = scheme_parameters[step]
            for function, kwargs in step_parameters.items():
                step_function = getattr(step, function)
                datas = step_function(processing_dict, scheme_dict, **kwargs) # returned data should be a dict with {label : data, [...]}
                for label, data in datas.items():
                    scheme_dict[step][label].update(data)

            return postprocessing_scheme(processing_dict, scheme_dict, scheme_steps[1:], scheme_parameters, processing_steps)

        for scheme_name, scheme_parameters in schemes.items():
            scheme_steps = scheme_parameters.keys()
            postprocessing_dict[scheme_name] = postprocessing_scheme(processing_dict = processing_dict.copy(),
                                                                     scheme_dict = {},
                                                                     scheme_steps = scheme_steps.copy(),
                                                                     scheme_parameters = scheme_parameters.copy(),
                                                                     processing_steps = processing_steps)

        return postprocessing_dict
        '''


    def report():
        pass

    def save():
        pass

    def nest_data(steps, data):
        if len(steps) == 0:
            return data
        if len(steps) == 1:
            return {f"no_{steps[0]}" : data}
        return {f"no_{steps[0]}" : nest_data(steps[1:], data)}

    def unnest_data(d):
        print(list(d.keys()))
        if len(d.keys()) > 1:
            raise Exception("There shouldn't be more than one key at this step.")
        value = d[list(d.keys())[0]]
        if isinstance(value, dict):
            return unnest_data(value)
        return value

    return preprocessing, processing, postprocessing


if __name__ == "__main__":
    file_path_list = glob.glob("DATA/*.fif")
    start = time.perf_counter()
    preprocessing, processing, postprocessing = main(file_path_list = file_path_list, parameters = PARAMETERS)
    processing_dict = preprocessing()
    processing(main_dict = processing_dict, steps = list(PARAMETERS['processing'].keys()), nstep = 0, info = {})
    postprocessing_dict = postprocessing(processing_dict = processing_dict, parameters = PARAMETERS)
    end = time.perf_counter()
    print(f"duration : {end-start}")

