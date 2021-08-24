#!/usr/bin/env python3

import os
import subprocess
from subprocess import CalledProcessError

from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

"""Module for running the 01_data_clean R script that helps process the 
   FAOSTAT data for preparing the SIMPLE database.
"""

class SimpleDataClean(GeoEDFPlugin):

    # required inputs are:
    # (1) input directory where the CSV files from FAO have been stored
    # (2) start year
    # (3) end year
    # optional inputs can override the region, crop, and livestock sets

    __optional_params = ['regsets_csv','cropsets_csv','livestocksets_csv']

    __required_params = ['fao_input_dir','start_year','end_year']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
               raise GeoEDFError('Required parameter %s for SimpleDataClean not provided' % param)
           
        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            #if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # fetch static reg, crop, and livestock set CSVs that are packaged with processor
        # if no overrides have been provided
        # look in setup.py data_files for location where these have been placed
        if self.regsets_csv is None:
            self.regsets_csv = '/usr/local/data/reg_sets.csv'
        if self.cropsets_csv is None:
            self.cropsets_csv = '/usr/local/data/crop_sets.csv'
        if self.livestocksets_csv is None:
            self.livestocksets_csv = '/usr/local/data/livestock_sets.csv'

        # also fetch the static region maps csv; this file is always packaged with the processor
        self.regmaps_csv = '/usr/local/data/reg_map.csv'

        # finally, the R script that needs to be executed
        # this is stored at /usr/local/bin
        self.data_clean_script = '/usr/local/bin/01_data_clean.r'

        # validate start and end years
        try:
            if int(self.start_year) > int(self.end_year):
                raise GeoEDFError('start_year must be smaller than end_year in SimpleDataClean')
        except:
            raise GeoEDFError('Error occurred when validating start_year and end_year for SimpleDataClean; make sure they are integers')

        # super class init
        super().__init__()

    # the process method that calls the 01_data_clean.r script 
    def process(self):

        # the R script is invoked with the following command line arguments:
        # 1. start year
        # 2. end year
        # 3. input directory where FAO files are stored
        # 4. output directory
        # 5. region map csv path
        # 6. region sets csv path
        # 7. crop sets csv path
        # 8. livestock sets csv path

        # dummy init to catch error in stdout
        stdout = ''

        try:
            command = "Rscript"
            args = [str(self.start_year),str(self.end_year),self.fao_input_dir,self.target_path,self.regmaps_csv,self.regsets_csv,self.cropsets_csv,self.livestocksets_csv]

            cmd = [command, self.data_clean_script] + args

            stdout = subprocess.check_output(cmd,universal_newlines=True)

        except CalledProcessError:
            raise GeoEDFError('Error occurred when running SimpleDataClean processor: %s' % stdout)
            
            
        

    
