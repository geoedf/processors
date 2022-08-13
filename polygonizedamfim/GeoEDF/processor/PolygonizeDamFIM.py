#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import subprocess
import os

""" Module for implementing the PolygonizeDamFIM processor. This accepts a flood inundation map
    GeoTIFF as input and returns a shapefile that has been reclassified and reduced in scale.
"""

class PolygonizeDamFIM(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['rasterfile']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for PolygonizeDamFIM not provided' % param)

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
        
        try:
            geojson_out = "%s/damfim.json" % self.target_path
            
            subprocess.run(["gdal_polygonize.py",self.rasterfile,geojson_out,"-b","1","damfim","depth"])
            
        except:
            raise GeoEDFError("Error occurred running gdal_polygonize to convert FIM Tiff %s" % os.path.split(self.rasterfile)[1])
        
