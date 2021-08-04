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

""" Module for clipping a raster to the extents of a given mask layer as a Shapefile.
    The two files may be in different projections; here we reproject to the mask layer's
    projection. The raster can be in any standard raster format
"""

class ClipRasterByMask(GeoEDFPlugin):

    # in workflow mode, the destination directory will be provided
    # only a directory/folder of rasters is required
    __optional_params = []
    __required_params = ['raster_file','mask_shapefile']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for ClipRasterByMask not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        super().__init__()

    # the process method that performs the masking of raster by the mask layer
    # first reproject raster to mask layer's projection
    # then clip reprojected raster to the mask layer's extents
    def process(self):
        
        # QGIS initialization
        try:
            qgs = QgsApplication([], False)
            qgs.initQgis()
            Processing.initialize()
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        except:
            raise GeoEDFError('Error when initializing QGIS in ClipRasterByMask processor!')

        #determine mask layer's projection
        try:
            input_crs = QgsVectorLayer(self.mask_shapefile, '', 'ogr' ).crs().authid()
        except:
            raise GeoEDFError('Error determining projection of mask layer: %s in ClipRasterByMask' % os.path.split(self.mask_shapefile)[1])

        # now reproject raster
        try:
            # path to temp reprojected file
            reprojected_raster = '%s/reprojected.tif' % self.target_path
            processing.run('gdal:warpreproject', {'INPUT': self.raster_file, 'TARGET_CRS': input_crs, 'OUTPUT': reprojected_raster})
        except:
            raise GeoEDFError('Error reprojecting raster file to mask layer projection in ClipRasterByMask!')
            
        # finally clip the reprojected raster
        try:
            # path to final output file
            clipped_raster = '%s/clipped.tif' % self.target_path
            processing.run('gdal:cliprasterbymasklayer',{'INPUT': reprojected_raster, 'MASK': self.mask_shapefile, 'OUTPUT': clipped_raster})
        except:
            raise GeoEDFError('Error clipping raster to mask extents in ClipRasterByMask!')

        # delete the intermediate reprojected raster file since we don't want it to be picked up
        # in subsequent workflow steps
        os.remove(reprojected_raster)
        
        

        
        



                    


                    

            
            

        






