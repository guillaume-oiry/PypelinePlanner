import copy


def view(main_dict, view_parameters, parameters):

    # 1 - Create the tree of the view dictionnary
    view = create_tree(view_parameters)
    print(f"NEW TREE : {view}")

    # 2 - Fill the tree of the view dictionnary according to conditions
    view = fill_tree(
        main_dict=main_dict,
        view_parameters=view_parameters,
        steps=["file_path", *list(parameters["processing"].keys())],
        nstep=0,
        view=view,
        info={},
    )

    return view


def create_tree(view_parameters, view={}):

    # The view dict will be nested at a step only if there are several possible conditions,
    # so only if conditions are registered as list or dict of conditions.

    view_parameters = {
        key: value
        for key, value in view_parameters.items()
        if (isinstance(value, list) or isinstance(value, dict))
    }

    for key, value in view_parameters.items():

        if isinstance(value, list):
            for c in value:
                view[c] = {}
                next_view_parameters = copy.deepcopy(view_parameters)
                del next_view_parameters[key]
                create_tree(next_view_parameters, view[c])

        elif isinstance(value, dict):
            for c in value.keys():
                view[c] = {}
                next_view_parameters = copy.deepcopy(view_parameters)
                del next_view_parameters[key]
                create_tree(next_view_parameters, view[c])

        return view


def fill_tree(main_dict, view_parameters, steps, nstep=0, view={}, info={}):

    if nstep >= len(steps):
        return

    for key, value in main_dict.items():

        info[steps[nstep]] = key

        # If the value is a dict we are not at the bottom file level yet.
        if type(value) is dict:
            fill_tree(
                main_dict[key],
                steps,
                view_parameters,
                nstep=nstep + 1,
                view=view,
                info=info,
            )

        else:
            check = True
            path = []
            for step, condition in view_parameters.items():
                check, path = check_conditions(check, path, step, condition, info)
            if check:
                view = update_tree(view, path, value)

    return view


def check_conditions(check, path, step, condition, info):
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


def update_tree(view, path, value):
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
