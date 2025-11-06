import modules
from parameters import PARAMETERS
import glob
import warnings

file_path_list = glob.glob("DATA/*.fif")

def main(file_path_list = file_path_list, parameters = PARAMETERS):

    def preprocessing():
        main_dict = {}
        preprocessing_options = parameters['preprocessing'].values()
        for file_path in file_path_list:
            option = [opt['PARAMETERS'] for opt in preprocessing_options if opt['CONDITION'](file_path)]
            if len(option) == 0 :
                warnings.warn(f"No conditions matching for {file_path}")
            elif len(option) > 1 :
                raise Exception(f"Condition should be mutually exclusive. {len(option)} conditions matched for {file_path}")
            else :
                option = option[0]
            function = list(option.keys())[0]
            # need error handling here ?
            kwargs = option[function]
            preprocessing_function = getattr(modules.preprocess, function)
            raw = preprocessing_function(file_path, parameters = kwargs, info=file_path)
            main_dict[file_path[5:]] = nest_data(list(parameters['processing'].keys()), raw) #not pretty the removal of 'DATA'
        return main_dict

    def processing(main_dict, steps = list(parameters['processing'].keys()), nstep = 0, info = {}):

        print(f'nstep : {nstep}')

        if len(steps) == 0:
            return main_dict

        if nstep >= len(steps):
            return main_dict

        step = steps[nstep]
        step_module = getattr(modules.process, step)
        processing_step_options = parameters['processing'][step]
        for key in main_dict.keys():
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
            return processing(main_dict[key], steps, nstep = nstep+1, info = info)

    def postprocessing(main_dict, processing_steps = parameters['processing'].keys(), schemes = parameters['postprocessing']):

        def postprocessing_scheme(main_dict, scheme_dict, scheme_steps, scheme_parameters, processing_steps = processing_steps):

            if len(scheme_steps) == 0:
                return scheme_dict
            
            step = scheme_steps[0]
            step_parameters = scheme_parameters[step]
            for function, kwargs in step_parameters.items():
                step_function = getattr(step, function)
                datas = step_function(main_dict, scheme_dict, **kwargs) # returned data should be a dict with {label : data, [...]}
                for label, data in datas.items():
                    scheme_dict[step][label].update(data)

            return postprocessing_scheme(main_dict, scheme_dict, scheme_steps[1:], scheme_parameters, processing_steps)

        postprocessing_dict = {}

        for scheme_name, scheme_parameters in schemes.values():
            scheme_steps = scheme_parameters.keys()
            postprocessing_dict[scheme_name] = postprocessing_scheme(main_dict = main_dict.copy(),
                                                                     scheme_dict = {},
                                                                     scheme_steps = scheme_steps.copy(),
                                                                     scheme_parameters = scheme_parameters.copy(),
                                                                     processing_steps = processing_steps)

        return postprocessing_dict

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
    main()

