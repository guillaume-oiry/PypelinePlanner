PARAMETERS = {'preprocessing' : {'sart' : {'CONDITION' : lambda file_path : 'task-sart' in file_path,
                                           'PARAMETERS' : {'EPICE_minimal_preprocessing' : {'LOW_FREQ' : 0.1,
                                                                                            'HIGH_FREQ' : 40,
                                                                                            'NOTCH_FILTER' : 50}}},
                                 'other' : {'CONDITION' : lambda file_path : True,
                                            'PARAMETERS' : {'EPICE_minimal_preprocessing' : {'LOW_FREQ' : 0.1,
                                                                                            'HIGH_FREQ' : 40,
                                                                                            'NOTCH_FILTER' : 50}}}},
              'processing' : {'extraction' : {'all' : {'CONDITIONS' : lambda info : True,
                                                       'PARAMETERS' : {'subset_epoching' : {'tmin' : -20,
                                                                                            'tmax' : 0,
                                                                                            'ptp_threshold' : None,
                                                                                            'reject_flat' : 1e-6,
                                                                                            'add_df' : False,
                                                                                            'labels' : {'probe':'probe'} 
                                                                                            }
                                                                       }
                                                       }
                                              }
                              },
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
