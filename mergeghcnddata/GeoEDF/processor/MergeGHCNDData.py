#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd
import os

""" Module for implementing the processor for merging per-station GHCND data. This plugin will process 
    a directory containing per-station,per-parameter CSV files. It merges the data, producing a single CSV
    file for each parameter. Each column in this result CSV corresponds to a station.
"""

class MergeGHCNDData(GeoEDFPlugin):

    # GHCND params are hardcoded for now
    __optional_params = []
    __required_params = ['data_dir']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for MergeGHCNDData not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            
        # set the hardcoded set of meterological params
        # can possibly generalize to fetch any list of params in the future
        self.met_params = ['SNOW','SNWD','TMAX','TMIN','PRCP']

        # class super class init
        super().__init__()

    # each Process plugin needs to implement this method
    # if error, raise exception; if not, return True
    def process(self):

        # Not much validation, only process csv files with names matching the 
        # stationID_param.csv pattern
        # first go through data directory collecting station files for each param
        # initialize dicts to hold these filenames and the final merged DFs
        met_param_files = dict()
        met_param_data = dict()
        for met_param in self.met_params:
            met_param_files[met_param] = []
            met_param_data[met_param] = pd.DataFrame()
                
        # loop through files
        for file_or_dir in os.listdir(self.data_dir):
            if file_or_dir.endswith('.csv'):
                basename = os.path.splitext(file_or_dir)[0]
                try:
                    station_id,param = basename.split('_',maxsplit=2)
                    if param in self.met_params:
                        fullpath = '%s/%s' % (self.data_dir,file_or_dir)
                        met_param_files[param].append(fullpath)
                except ValueError:
                    print('File %s not being processed; does not match pattern' % file_or_dir)
                        
        # now for each param merge the data frames
        for met_param in self.met_params:
            try:
                for station_file in met_param_files[met_param]:
                    station_df = pd.read_csv(station_file)
                    # get rid of dummy index
                    station_df.set_index(pd.to_datetime(station_df['date']), inplace=True)
                    # extract station ID to use as column name
                    station_filename = os.path.split(station_file)[1]
                    basename = os.path.splitext(station_filename)[0]
                    station_id = basename.split('_')[0]
                    # now keep only the data column
                    station_df = station_df.filter([met_param])
                    # rename data column to station ID
                    # this is so that we can merge individual station DFs via outer joins
                    station_df = station_df.rename(columns={met_param: station_id})
                    if met_param_data[met_param].empty:
                        met_param_data[met_param] = station_df
                    else:
                        met_param_data[met_param] = met_param_data[met_param].merge(station_df,how='outer',left_index=True,right_index=True)
                # fill NaN with zeros
                met_param_data[met_param] = met_param_data[met_param].fillna(value=0)
            except:
                raise GeoEDFError("Error merging station data for param %s in MergeGHCDData" % met_param)
                
        # write out per parameter csv files
        for met_param in self.met_params:
            try:
                met_param_datafile = '%s/%s.csv' % (self.target_path,met_param)
                met_param_data[met_param].to_csv(met_param_datafile)
            except:
                raise GeoEDFError('Error writing out data frame for param %s in MergeGHCNDData' % met_param)
                
        return True
            
                        
             
                        

