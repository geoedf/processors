#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from qgis.core import *
from qgis.analysis import QgsNativeAlgorithms
import processing
from processing.core.Processing import Processing 

from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

os.environ['QT_QPA_PLATFORM']='offscreen'

""" Module for merging a directory of rasters which are in the ArcGrid format
    The QGIS gdal:merge processor is used to merge the given rasters
    Given a directory input, the subdirectories with names beginning in "grd"
    are assumed to hold an ArcGrid raster file and used as the input list of 
    raster to merge
"""

class MergeArcGridRasters(GeoEDFPlugin):

    # in workflow mode, the destination directory will be provided
    # only a directory/folder of rasters is required
    __optional_params = []
    __required_params = ['input_folder']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for MergeArcGridRasters not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        super().__init__()

    # the process method that performs the raster merging operation and saves resulting 
    # merged raster GeoTiff file to the target directory. 
    def process(self):
        
        # QGIS initialization
        try:
            qgs = QgsApplication([], False)
            qgs.initQgis()
            Processing.initialize()
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        except:
            raise GeoEDFError('Error when initializing QGIS in MergeArcGridRasters processor!')

        # identify rasters to be merged
        input_raster_list = []
        for file_or_dir in os.listdir(self.input_folder):
            file_or_dir_path = os.path.join(self.input_folder,file_or_dir)
            if os.path.isdir(file_or_dir_path) & file_or_dir.startswith("grd"):
                input_raster_list.append(file_or_dir_path)

        # check if any rasters found
        if len(input_raster_list) == 0:
            raise GeoEDFError('No rasters found to merge in MergeArcGridRasters')

        # now merge them
        try:
            output_raster = "%s/merged_raster.tif" % self.target_path
            processing.run("gdal:merge",{'INPUT':input_raster_list,'OUTPUT':output_raster})
        except:
            raise GeoEDFError('Error when merging input rasters in MergeArcGridRasters')
        

        
        



                    


                    

            
            

        






