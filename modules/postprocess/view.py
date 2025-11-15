import copy

def view(main_dict, view_parameters, parameters):

    # 1 - Create the tree of the view dictionnary
    view = create_tree(view_parameters)
    print(f"NEW TREE : {view}")


    # 2 - Fill the tree of the view dictionnary according to conditions
    view = fill_tree(main_dict = main_dict,
                     view_parameters = view_parameters,
                     steps = ['file_path', *list(parameters['processing'].keys())],
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
            print(info)
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
                print("all conditions are met")
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

