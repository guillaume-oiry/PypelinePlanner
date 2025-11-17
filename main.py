import modules
from parameters import PARAMETERS
import glob
import warnings
import copy
import multiprocessing
import time


def main(file_path_list, parameters):

    def preprocessing(mp = True):

        print("starting preprocessing")

        if mp:
            q = multiprocessing.Queue()
            mp_list = []
            def mp_preprocess(q, preprocessing_function, file_path, parameters, info):
                data = preprocessing_function(file_path, parameters = kwargs, info=file_path)
                q.put((file_path, data))

        preprocessing_dict = {}
        preprocessing_options = parameters['preprocessing'].values()

        for file_path in file_path_list:

            option = [opt['PARAMETERS'] for opt in preprocessing_options if opt['CONDITION'](file_path)]
            if len(option) == 0 :
                warnings.warn(f"No conditions matching for {file_path}")
            elif len(option) > 1 :
                raise Exception(f"Conditions should be mutually exclusive. {len(option)} conditions matched for {file_path}")
            else :
                option = option[0]
            function = list(option.keys())[0] # so only one preprocessing function by file
            # need error handling here ?
            kwargs = option[function]
            preprocessing_function = getattr(modules.preprocess, function)

            if mp:
                process = multiprocessing.Process(target=mp_preprocess, args=(q, preprocessing_function, file_path, kwargs, file_path))
                process.start()
                mp_list.append(process)
            else:
                data = preprocessing_function(file_path, parameters = kwargs, info=file_path)
                preprocessing_dict[file_path] = nest_data(list(parameters['processing'].keys()), data)

        if mp:

            for _ in mp_list:
                file_path, data = q.get()
                preprocessing_dict[file_path] = nest_data(list(parameters["processing"].keys()), data)

            for p in mp_list:
                p.join()
                p.close()

        return preprocessing_dict

    def processing(main_dict, steps = list(parameters['processing'].keys()), nstep = 0, info = {}, mp = True):

        print("starting processing")
        
        def rec_processing(ind_dict, steps = list(parameters['processing'].keys()), nstep = 0, info = {}):

            if len(steps) == 0:
                return ind_dict

            if nstep >= len(steps):
                return ind_dict

            step = steps[nstep]
            step_module = getattr(modules, step)
            processing_step_options = parameters['processing'][step]
            for key in ind_dict.keys():
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
                    datas = step_function(unnest_data(ind_dict[key]), info, **kwargs) # returned data should be a dict with {label : data, [...]}
                    for label, data in datas.items():
                        ind_dict[key].update({label : nest_data(steps = steps[nstep+1:], data = data)})
                rec_processing(ind_dict[key], steps, nstep = nstep+1, info = info)
            return ind_dict

        if mp:
            q = multiprocessing.Queue()
            mp_list = []
            def mp_process(q, file_path, ind, parameters):
                ind_dict = rec_processing(ind_dict = {file_path : ind}, steps = list(parameters['processing'].keys()), nstep = 0, info = {})
                q.put(ind_dict)

        processing_dict = {}

        for file_path, ind in main_dict.items():

            if mp:
                process = multiprocessing.Process(target=mp_process, args=(q, file_path, ind, parameters))
                process.start()
                mp_list.append(process)

            else:
                ind_dict = rec_processing(ind_dict = {file_path : ind}, steps = list(parameters['processing'].keys()), nstep = 0, info = {})
                for key, value in ind_dict.items():
                    processing_dict[key] = value

        if mp:

            for _ in mp_list:
                ind_dict = q.get()
                for key, value in ind_dict.items():
                    processing_dict[key] = value

            for p in mp_list:
                p.join()
                #p.close()

        return processing_dict

    def postprocessing(processing_dict, parameters, mp = True):

        print("starting postprocessing")

        postprocessing_dict = {}
        postprocessing_parameters = parameters['postprocessing']

        if mp:
            q = multiprocessing.Queue()
            mp_list = []
            def mp_postprocess(q, postprocessing_function, parameters, kwargs, function):
                data = postprocessing_function(copy.deepcopy(processing_dict), parameters, **kwargs) # returned data should be a dict with {label : data, [...]}
                q.put((function, data))

        for function, kwargs in postprocessing_parameters.items():

            postprocessing_function = getattr(modules.postprocessing_functions, function)
            #data = postprocessing_function(copy.deepcopy(processing_dict), parameters, **kwargs) # returned data should be a dict with {label : data, [...]}

            if mp:
                process = multiprocessing.Process(target=mp_postprocess, args=(q, postprocessing_function, parameters, kwargs, function))
                process.start()
                mp_list.append(process)
            else:
                data = postprocessing_function(copy.deepcopy(processing_dict), parameters, **kwargs) # returned data should be a dict with {label : data, [...]}
                postprocessing_dict[function] = data

        if mp:

            for _ in mp_list:
                function, data = q.get()
                postprocessing_dict[function] = data

            for p in mp_list:
                p.join()
                p.close()

        return postprocessing_dict

        '''

        # DRAFT OF ANOTHER APPROACH TO POSTPROCESSING


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

    #multiprocessing.set_start_method('spawn')

    file_path_list = glob.glob("DATA/*.fif")

    preprocessing, processing, postprocessing = main(file_path_list = file_path_list, parameters = PARAMETERS)

    stats = []

    for mp in [True, False]:
        start_global = time.perf_counter()

        start_preprocessing = time.perf_counter()
        processing_dict = preprocessing(mp = mp)
        end_preprocessing = time.perf_counter()
        duration_preprocessing = end_preprocessing - start_preprocessing

        start_processing = time.perf_counter()
        processing_dict = processing(main_dict = processing_dict, steps = list(PARAMETERS['processing'].keys()), nstep = 0, info = {}, mp = mp)
        print(processing_dict)
        end_processing = time.perf_counter()
        duration_processing = end_processing - start_processing

        start_postprocessing = time.perf_counter()
        postprocessing_dict = postprocessing(processing_dict = processing_dict, parameters = PARAMETERS, mp = mp)
        end_postprocessing = time.perf_counter()
        duration_postprocessing = end_postprocessing - start_postprocessing

        end_global = time.perf_counter()
        duration_global = end_global - start_global

        stat = f"MP {mp} : {duration_global}\n - preprocessing : {duration_preprocessing}\n - processing : {duration_processing}\n - postprocessing : {duration_postprocessing}\n"
        stats.append(stat)

    for s in stats:
        print(s)

