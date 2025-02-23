PARAMETERS = {'preprocessing' : {'sart' : {'CONDITION' : lambda file_path : 'task-sart' in file_path,
                                           'PARAMETERS' : {'EPICE_minimal_preprocessing' : {'LOW_FREQ' : 0.1,
                                                                                            'HIGH_FREQ' : 40,
                                                                                            'NOTCH_FILTER' : 50}}},
                                 'other' : {'CONDITION' : lambda file_path : True,
                                            'PARAMETERS' : {'EPICE_minimal_preprocessing' : {'LOW_FREQ' : 0.1,
                                                                                            'HIGH_FREQ' : 40,
                                                                                            'NOTCH_FILTER' : 50}}}},
              'processing' : {'extraction' : {},
                              'cleaning' : {},
                              'analysis' : {},
                              'plot' : {}},
              'postprocessing' : {'scheme1' : {'views' : {'func1' : {}},
                                               'statistics' : {'func1' : {},
                                                               'func2' : {}},
                                               'figures' : {'func1' : {},
                                                            'func2' : {},
                                                            'func3' : {}
                                                            }
                                               }
                                  }
              }

'''
postprocessing_dict = {'scheme1' : {'floor1-a' : {'data' : data,
                                                  'statistics' : {'func1' : {},
                                                                  'func2' : {}},
                                                  'figures' : {'func1' : {},
                                                               'func2' : {},
                                                               'func3' : {}}},
                                    'floor1-b' : {'data' : data,
                                                  'statistics' : statistics,
                                                  'figures' : figures}}}
'''


