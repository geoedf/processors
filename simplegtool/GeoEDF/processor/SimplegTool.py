#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import geopandas as gpd
import glob
import os
import subprocess
from os import walk
import re
import glob
import shutil

from pathlib import Path
""" Module for implementing the SimplegTool processor. 
"""

class SimplegTool(GeoEDFPlugin):
    # input directory or shapefile params are XOR
    # shapefile will take precedence
    # if end is provided, period also needs to be provided
    __optional_params = []
    __required_params = ['har_input_dir', 'target_year']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for SimplegTool not provided' % param)

        
        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # class super class init
        super().__init__()

    # each Processor plugin needs to implement this method
    # if error, raise exception
    # assume this method is called only when all params have been fully instantiated
    def process(self):

        self.move_har_to_YYYY()
        
        self.copy_simpleg_to_target_path()
        
        exec_dir = self.target_path+"/simpleg/02_data_proc"
        exec_path = exec_dir +"/02_data_proc"
        cmf_path  = exec_dir +"/02_data_proc.cmf"
        output_har_dir = exec_dir+"/out"
        
        self.edit_CMF_target_path(cmf_path)
        
        
        try:
            #subprocess.call(["/bin/cp","-r", "/simpleg", self.target_path])
            subprocess.call([exec_path, "-cmf", cmf_path], cwd= exec_dir)
            # wildcard character is literally interpreted and cause no such file error
            #subprocess.check_output(["/bin/cp", output_har_dir+"/*.har", self.target_path])
            
            # working code 
            #subprocess.check_output("/bin/cp"+"  "+output_har_dir+"/*.har"+"  "+self.target_path, shell=True)
            
            har_files_to_copy = output_har_dir+"/*.har"
            self.copy_hars_to_destination(har_files_to_copy, self.target_path)
            
            
            #subprocess.call(["/bin/rm","-rf", self.target_path+"/simpleg/"])

        except:
            raise GeoEDFError('Error occurred when running Shapefile2GeoJSON processor')

            
    # Har files left in target_path will be returned to the users as final output
    # Copying files using subprocess with wildcard causes either failure or shell execution concern.
    # This function copies all har files in subdirectory of the target path to the topmost of the the target path
    def copy_hars_to_destination(self, pattern, destination_dir):
        for file in glob.glob(pattern):
            print(file)
            shutil.copy(file, destination_dir)
            
        
        
        
    def copy_simpleg_to_target_path(self):
        try:
            subprocess.call(["/bin/cp","-r", "/simpleg", self.target_path])

        except:
            raise GeoEDFError('Error occurred when copying simpleg to the writable target path')

    def move_har_to_YYYY(self):
        fnames = []
        regex=r'(?P<year>[1-9][0-9]{3,3})\_(?P<varname>(\w)+).har'

        for (dirpath, dirnames, filenames) in walk(self.har_input_dir):
            print("dirpath", dirpath)
            print("filenames", filenames)
            fnames.extend(filenames)
            print(fnames)
            break

        for filename in fnames:
            #print(filename)
            m = re.match(regex, filename)
            #print(m)
            if m != None:
                print("match:", filename)
                print("groupdict:", m.groupdict())
                # create YYYY directory
                Path( os.path.join(dirpath,m.group('year'))).mkdir(parents=True, exist_ok=True)
                src_filepath = os.path.join(dirpath, filename)
                dst_filepath = os.path.join(dirpath, m.group('year'), m.group('varname')+".har")
                shutil.copy( src_filepath , dst_filepath)
        
    # find predefined variable <YYYY_PATH>, and replace it with target_year's directory 
    def edit_CMF_target_path(self, cmf_path):
        
        target_year_path = os.path.join(self.har_input_dir,str(self.target_year)) 
        self.replace_string_in_file(cmf_path, "<YYYY_PATH>", target_year_path)
        
    def replace_string_in_file(self, filename, pattern, new_string):
        with open(filename, 'rt') as fin:
            s = fin.read()

            if pattern not in s:
                print('"{pattern}" not found in {filename}.'.format(**locals()))
                return

        with open(filename, 'wt') as fout:
            s = s.replace(pattern, new_string )
            fout.write(s)
