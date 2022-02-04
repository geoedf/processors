#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import importlib
import zipfile
import shutil

from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Module for executing any InVEST model using the model API entrypoints
"""

class InVESTModel(GeoEDFPlugin):

    __optional_params = []
    __required_params = ['model','model_input']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for InVESTModel not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
        
        self.kwargs = kwargs

        super().__init__()

    # the process method that executes the specific InVEST model with a dictionary
    # of args constructed from kwargs
    def process(self):

        # construct args from kwargs by deleting the required and optional params
        for arg in self.provided_params:
            self.kwargs.pop(arg)
            
        # assume for now that input is always a zip file
        # copy file to processor output dir and then unzip
        shutil.copy(self.model_input,self.target_path)
        
        # determine input filename
        model_input_filename = os.path.split(self.model_input)[1]
        with zipfile.ZipFile(self.target_path + '/' + model_input_filename, 'r') as zip_ref:
            zip_ref.extractall(self.target_path)
            
        # delete zip file
        os.remove(self.target_path + '/' + model_input_filename)

        # model dirname 
        model_dirname = os.path.splitext(model_input_filename)[0]
        
        # chdir to right path
        os.chdir(self.target_path + '/' + model_dirname)
        
        # workspace_dir
        self.kwargs['workspace_dir'] = os.getcwd()
        
        # use importlib to import the necessary model
        model_mname = 'natcap.invest.%s.%s' % (self.model,self.model)
        model_module = importlib.import_module(model_mname)
        model_module.execute(self.kwargs)
        
        # zip up folder again to return
        shutil.make_archive(self.target_path + '/' + model_dirname, 'zip', self.target_path + '/' + model_dirname)
