#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd
import os

""" Module for implementing the processor for merging a folder of CSV files. This plugin will merge CSV 
    files in a given folder into a single CSV file.
"""

class MergeCSVFiles(GeoEDFPlugin):

    __optional_params = ['basename']
    __required_params = ['filepath']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for MergeCSVFiles not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            
        # class super class init
        super().__init__()

    # each Process plugin needs to implement this method
    # if error, raise exception; if not, return True
    def process(self):

        # if optional basename is provided, use it as output filename
        if self.basename is not None:
            output_path = '%s/%s.csv' % (self.target_path,self.basename)
        else:
            output_path = '%s/output.csv' % self.target_path
       
        merge_df = None
        
        # loop through files
        for file_or_dir in os.listdir(self.filepath):
            if file_or_dir.endswith('.csv'):
                fullpath = '%s/%s' % (self.filepath,file_or_dir)
                try:
                    df = pd.read_csv(fullpath)
                    if merge_df is None:
                        merge_df = df
                    else:
                        merge_df = merge_df.merge(df,how='outer')
                except pd.errors.EmptyDataError:
                    pass
        #write out to output
        merge_df.to_csv(output_path,index=False)
                
        return True