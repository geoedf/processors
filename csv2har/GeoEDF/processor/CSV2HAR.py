#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
import numpy as np

from harpy import *

from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Module for converting a SIMPLE CSV file into a HAR file. This only works on CSV 
    files of a specific format; i.e. those that contain region-wise aggregate values 
    of some FAOSTAT dataset variable. The CSV needs to contain two columns; first the 
    region's code name and second the float value for that region.
"""

class CSV2HAR(GeoEDFPlugin):

    # in workflow mode, the destination directory will be provided
    # input csv file is required
    # har file with the same basename as the csv file is created
    __optional_params = []
    __required_params = ['csvfile']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFPlugin class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for CSV2HAR not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        super().__init__()

    # the process method that performs the conversion from csv to har format
    # the HARPY library is used to create the necessary header array objects from the data
    def process(self):
        
        # first read the CSV file to fetch the regions and their corresponding values
        regions = []
        vals = []

        # name of the data field
        data_key = None
        
        with open(self.csvfile,'r') as csvFileObj:
            reader = csv.DictReader(csvFileObj)
            for row in reader:
                # pre-process step only required once
                # determine the name of the data field
                if data_key is None:
                    if len(list(row.keys())) != 2:
                        raise GeoEDFError("Error in CSV2HAR when processing %s. Exactly two fields are required" % self.csvfile)
                    else:
                        # REG is one, what is the other?
                        for key in row.keys():
                            if key != 'REG':
                                data_key = key
                                break
                regions.append(row['REG'])
                vals.append(row[data_key])

        # now build the HAR file header
        # first create the HAR file object
        (ignore, csvFilename) = os.path.split(self.csvfile)
        basename = os.path.splitext(csvFilename)[0]
        harFilename = '%s/%s.har' % (self.target_path,basename)
        harFile = HarFileObj(harFilename)

        # create the two header array objects and set them to the file
        
        # first the region header
        # in this header, region names are always padded to 12 characters long
        reg_arr = np.array([reg.ljust(12) for reg in regions],dtype='<U12')
        reg_setNames = ['REG']
        reg_setElements = [[reg.ljust(12) for reg in regions]]
        reg_coeff_name = ''.ljust(12)
        reg_long_name = 'Set REG inferred from CSV file'.ljust(70)
        reg_header = HeaderArrayObj.HeaderArrayFromData(reg_arr,reg_coeff_name,reg_long_name,reg_setNames,dict(zip(reg_setNames,reg_setElements)))
        # add header to HAR file
        harFile["SET1"] = reg_header

        # then the csv data header
        csv_arr = np.array(vals,dtype='float32')
        csv_setNames = ['REG']
        csv_setElements = [regions]
        csv_coeff_name = 'CSVData'.ljust(12)
        csv_long_name = 'Array extracted from CSV'.ljust(70)
        csv_header = HeaderArrayObj.HeaderArrayFromData(csv_arr,csv_coeff_name,csv_long_name,csv_setNames,dict(zip(csv_setNames,csv_setElements)))
        harFile["CSV"] = csv_header

        # write out the HAR file
        harFile.writeToDisk()
