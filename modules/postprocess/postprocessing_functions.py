import numpy as np
import matplotlib.pyplot as plt
import copy

def psd_mean(processing_dict, parameters):

    #Format data for better manipulation
    view_parameters = {'file_path' : {'work' : lambda info : 'task-work' in info['file_path'],
                                      'sart' : lambda info : 'task-sart' in info['file_path']},
                       'extraction' : lambda info : 'epoch' in info['extraction'],
                       'analysis' : lambda info : 'psd' in info['analysis']}
    view_dict = view(processing_dict, view_parameters, parameters)

    #PSD mean (by context)
    psd_means = {}
    for context, psd_list in view_dict.items():
        psd_means[context] = {}
        concat = np.concatenate(psd_list, axis=0)
        psd_mean = np.mean(concat, axis=0)
        psd_means[context]['data'] = psd_mean
        psd_means[context]['plot'] = PSD_context_plot(data = psd_mean,
                                                      context = context,
                                                      ch = ['Fp1','Fp2','Fz','Cz','Pz','O1','O2'])

    return psd_means

def PSD_context_plot(data, context, ch):
    
    plot = {}

    data = np.log10(data)

    ndim = data.ndim
    if ndim == 3:
        data_std = np.std(data, axis=0)
        data = np.mean(data, axis=0)
    
    fig, ax = plt.subplots(
        nrows=1, ncols=1, figsize=(12, 12), layout = "constrained")
    
    freqs = np.linspace(0.5, 40, 80)
    for i in range(data.shape[0]):
        ax.plot(freqs, np.array(data[i]).T, label = ch[i], alpha = .8)
        if ndim == 3 :
            ax.fill_between(freqs, data[i] - data_std[i], data[i] + data_std[i], alpha = .1)
    
    # Set the title and labels
    ax.set_title(f'PSD {context}', fontsize=50)
    ax.set_xlabel('Frequency (Hz)', fontsize=30)
    ax.set_ylabel('(dB)', fontsize=30) # this is dB
    ax.set_xlim([0.5, 40])
    
    # ax.set_ylim([-30, 60])
    ax.legend()
    
    # Show the plot
    plt.legend(prop={'size':40})
    plt.close()
    
    return fig

def view(main_dict, view_parameters, parameters):

    # 1 - Create the tree of the view dictionnary
    view = create_tree(view_parameters)

    # 2 - Fill the tree of the view dictionnary according to conditions
    view = fill_tree(main_dict = main_dict,
                     steps = ['file_path', *list(parameters['processing'].keys())],
                     parameters = view_parameters,
                     nstep = 0,
                     view = view,
                     info = {})

    return view

def create_tree(parameters, view = {}):
    parameters = {key : value for key, value in parameters.items() if (isinstance(value, list) or isinstance(value, dict))}
    for key, value in parameters.items():
        if isinstance(value, list):
            for c in value:
                view[c] = {}
                next_parameters = copy.deepcopy(parameters)
                del next_parameters[key]
                create_tree(next_parameters, view[c])
        elif isinstance(value, dict):
            for c in value.keys():
                view[c] = {}
                next_parameters = copy.deepcopy(parameters)
                del next_parameters[key]
                create_tree(next_parameters, view[c])
        return view

def fill_tree(main_dict, steps, parameters, nstep = 0, view = {}, info = {}):
    if nstep >= len(steps):
        return
    for key, value in main_dict.items():
        info[steps[nstep]] = key
        if type(value) is dict:
            fill_tree(main_dict[key], steps, parameters, nstep = nstep + 1, view = view, info = info)
        else:
            
            # Check conditions and the details the path of the file
            path = []
            check = True
            for step, condition in parameters.items() :
                match str(type(condition)):
                    case "<class 'function'>":
                        if not condition(info):
                            check = False
                    case "<class 'bool'>":
                        path.append(info[step])
                    case "<class 'list'>":
                        if info(step) in condition:
                            path.append(info[step])
                        else:
                            check = False
                    case "<class 'dict'>":
                        dict_check = False
                        for category, cond in condition.items():
                            if cond(info):
                                path.append(category)
                                dict_check = True
                        if dict_check == False:
                            check = False
            
            # If all conditions are met copy the file to the view tree
            if check:
                if len(path) == 0:
                    if type(view[path[0]]) is dict:
                        view = [copy.deepcopy(value)]
                    elif type(view[path[0]]) is list:
                        view.append(copy.deepcopy(value))
                    continue
                while len(path) > 1:
                    view = view[path.pop(0)]
                if type(view[path[0]]) is dict:
                    view[path.pop(0)] = [copy.deepcopy(value)]
                elif type(view[path[0]]) is list:
                    view[path.pop(0)].append(copy.deepcopy(value))
                else:
                    raise Exception

    return view

