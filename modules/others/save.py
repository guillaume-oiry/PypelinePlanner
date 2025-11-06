import os
#import classes
import numpy as np
import pandas as pd

def save(main_dict, scheme_dict):

    def save_data(data_label, data):
        match data:
            case str() | bool() | int() | float():
                with open(f'{data_label}.txt', 'w') as output:
                    output.write(str(data))
            case np.ndarray():
                np.save(data_label, data)
            case pd.DataFrame():
                data.to_csv(data_label)

    def save_dict(upper_key, dictionary):
        #os.getcwd()
        os.mkdir(upper_key)
        os.chdir(upper_key)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                save_dict(key, value)
            else :
                save_data(key, value)

