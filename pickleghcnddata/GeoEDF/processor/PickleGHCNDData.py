#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd
import os
import pickle

""" Module for implementing the processor for creating a pickle file from rolling 7 and 30-day windows of 
    per-parameter GHCND data. This plugin assumes the files are named <param>.csv. This plugin will process 
    a directory containing these per-parameter CSV files. It creates one pickle file per parameter. 
"""

class PickleGHCNDData(GeoEDFPlugin):

    # GHCND params are hardcoded for now
    __optional_params = []
    __required_params = ['data_dir']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for PickleGHCNDData not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            
        # set the hardcoded set of meterological params
        self.met_params = ['SNOW','SNWD','TMAX','TMIN','PRCP']

        # class super class init
        super().__init__()

    # each Process plugin needs to implement this method
    # if error, raise exception; if not, return True
    def process(self):

        # Not much validation, only process csv files with names matching the 
        # param.csv pattern
        # load the data into Pandas dataframe and create the rolling windows
        for met_param in self.met_params:
            # check to see if this param file exists
            fullpath = '%s/%s.csv' % (self.data_dir,met_param)
            if os.path.isfile(fullpath):
                # load into DF
                met_df = pd.read_csv(fullpath)
                
                # fill nulls
                met_df = met_df.fillna(value=0)
                
                #since we want 7 and 30 day windows, make sure we have atleast 32 rows
                num_rows = met_df.shape[0]
                
                if num_rows < 32:
                    print("PickleGHCNDData: Cannot create pickle file for %s due to insufficient data records, need atleast 32" % met_param)
                    continue
                # continue with getting rolling windows
                try:
                    met_df_origin = met_df[32:]
                    met_df_lag1 = met_df[31:-1]
                    met_df_30day = met_df.rolling(window=30).sum()
                    met_df_7day = met_df.rolling(window=7).sum()
                
                    # moving averages
                    met_df_30day = met_df_30day[32:]
                    met_df_7day = met_df_7day[32:]
                    
                except:
                    raise GeoEDFError("Error occurred computing rolling windows for %s in PickleGHCNDData" % met_param)
                    
                # create dictionary to output to pickle file
                datasets = {}
                datasets[met_param] = met_df_origin
                datasets[met_param+'_lag1'] = met_df_lag1
                datasets[met_param+'_30D'] = met_df_30day
                datasets[met_param+'_7D'] = met_df_7day
                
                out_dict = {'Data_all':list(datasets.values()), 'df_name':list(datasets.keys())}
                
                # output to file
                try:
                    pickle_filename = '%s/%s_HUC2.p' % (self.target_path,met_param)
                    with open(pickle_filename,'wb') as pickle_file:
                        pickle.dump(out_dict,pickle_file)
                except:
                    raise GeoEDFError("Error writing out pickle file for % in PickleGHCNDData" % met_param)
                    
        return True
            
                        
             
                        

