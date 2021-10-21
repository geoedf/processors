#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import geopandas as gpd
import glob
import os
from os import walk
import subprocess
import re
import shutil

from pathlib import Path

class SimplegTool(GeoEDFPlugin):
    """ Module for running 02_data_proc binary file that generates
        two database files ( LANDDATA.har, DATACHKS.har).

        SimplegTool requires two parameters:
        1) har_input_dir : directory where INC, POP, QCROP, VCROP, QLAND data exist
        2) target_year : base year

        An economic model (02_data_proc.tab) is compiled into a Fortran code by GEMPACK
        program(copsmodels.com), and then transforms into an executable named 02_data_proc.

        The resulting executable/binary takes a command file (CMF) that instructs
        model to load inputs(INC, POP, QCROP, and so on). 
        User needs to edit the cmf file in order to select the base year(which is 
        same as target_year,one of the required parameters). User specified target_year
        will be automatically set in the command file through edit_CMF_target_path().

        Remember that base year or target_year must fall within start_year and 
        end_year of the SimpleDataClean processor.

        Input Data files  (see input folder)!    
        --------------------------------------     
        FILE INC_DAT   # real GDP (in USD 2005) #;
        FILE POP_DAT   # population (in numbers) #;
        FILE QCROP_DAT # aggregate crop output (in corn. eq. MTs) #;
        FILE VCROP_DAT # Value of aggregate crop output (in USD) #;
        FILE QLAND_DAT # cropland (in ha) #;
        ------------------------------------------

        Note that SimplegTool processor modifies CSV2HAR processor's output directory.
        It copies YYYY_variable.har files to YYYY/variable.har because the command file
        reads inputs from the baHar files left in target_path will be returned to the users as final output.
                Turns out that copying files using subprocess with wildcard causes 
                either failure or shell execution concern.
                This function copies all har files in subdirectory of the target path 
                to the destination directory.se_year/variable.har.
        Please refer to move_har_to_YYYY() for details.

    """
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

        # restructure CSV2HAR output directory structure
        self.move_har_to_YYYY()
        
        #Singualarity container cannot modify its file system.
        #The binary modifies the same directory where it sits in.
        #Therefore /simpleg directory is copied to the writable output directory
        #of the SimplegTool processor, and the final HAR files are copied to the topmost
        #directory of the SimplegTool output directory.
        self.copy_simpleg_to_target_path()
        
        # the directory simpleg binary is located at
        exec_dir = self.target_path+"/simpleg/02_data_proc"
        # the executable path 
        exec_path = exec_dir +"/02_data_proc"
        # the command file path 
        cmf_path  = exec_dir +"/02_data_proc.cmf"
        # directory that model binary produces .har files
        output_har_dir = exec_dir+"/out"
        
        #make command file to look up given base year's input data
        self.edit_CMF_target_path(cmf_path)
        
        
        try:
            subprocess.call([exec_path, "-cmf", cmf_path], cwd= exec_dir)
            # Not working 
            # wildcard character is literally interpreted and cause no such file error
            #subprocess.check_output(["/bin/cp", output_har_dir+"/*.har", self.target_path])
            
            # Working  
            #subprocess.check_output("/bin/cp"+"  "+output_har_dir+"/*.har"+"  "+self.target_path, shell=True)
            
            # want to copy all har files model binary produced
            har_files_to_copy = output_har_dir+"/*.har"
            
            self.copy_hars_to_destination(har_files_to_copy, self.target_path)
            
            
            #subprocess.call(["/bin/rm","-rf", self.target_path+"/simpleg/"])

        except:
            raise GeoEDFError('Error occurred when running SimplegTool processor')

            

    def copy_hars_to_destination(self, pattern, destination_dir):
        """ Copy har files matching the given pattern to the destination directory
    
            Har files left in target_path will be returned to the users as final output.
            Turns out that copying files using subprocess with wildcard causes 
            either failure or shell execution concern.
            This function copies all har files in subdirectory of the target path 
            to the destination directory.
        """
        for file in glob.glob(pattern):
            print(file)
            shutil.copy(file, destination_dir)
            
        
        

    def copy_simpleg_to_target_path(self):
        """ Copy /simpleg directory of the Singularity container to output directory.
    
            This is to circumvent the read-only limitation of the Singularity container.
            The directory /simpleg is copied to 
            a temporary execution place, output directory of the SimplegTool processor,
            and then executable is invoked.
        """
        try:
            subprocess.call(["/bin/cp","-r", "/simpleg", self.target_path])

        except:
            raise GeoEDFError('Error occurred when copying simpleg to the SimplegTool output directory')

            
            

    def move_har_to_YYYY(self):
        """ Finds all YYYY_alphanumeric.har files and move them to YYYY directory.
        
            Year component is removed from the filename. 
        """
        
        fnames = []
        regex=r'(?P<year>[1-9][0-9]{3,3})\_(?P<varname>(\w)+).har'

        # get a list of files in har_input_dir
        for (dirpath, dirnames, filenames) in walk(self.har_input_dir):
            print("dirpath", dirpath)
            print("filenames", filenames)
            fnames.extend(filenames)
            print(fnames)
            break

        # if YYYY_variable.har is found, copy it to YYYY/variable.har
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
        

    def edit_CMF_target_path(self, cmf_path):
        """ find predefined variable <YYYY_PATH> in command file, 
            and replace it with target_year's directory.

            ex, FILE INC_DAT   = <YYYY_PATH>/INC.har;
                may be replaced with 
                FILE INC_DAT   = /data/37393048/3/2005/INC.har"
        """
        target_year_path = os.path.join(self.har_input_dir,str(self.target_year)) 
        self.replace_string_in_file(cmf_path, "<YYYY_PATH>", target_year_path)
    
    
    
   
    def replace_string_in_file(self, filename, pattern, new_string):
        """ Update paths in the command file(CMF).
    
            Input HAR file paths are at the CSV2HAR output directory.
            This function updates input HAR file paths in command file so that
            it can correctly look up inputs. It finds all occurrence of "pattern" 
            from "filename" and replace them with "new_string". 
        """
        with open(filename, 'rt') as fin:
            s = fin.read()

            if pattern not in s:  # if not found, do not replace anything.
                print('"{pattern}" not found in {filename}.'.format(**locals()))
                return

        with open(filename, 'wt') as fout: # if found, replace all <YYYY_PATH> with target year's directory
            s = s.replace(pattern, new_string )
            fout.write(s)
