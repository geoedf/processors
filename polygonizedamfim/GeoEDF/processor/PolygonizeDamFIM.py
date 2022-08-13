#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd
import geopandas as gpd
import xarray as xr
from xrspatial.classify import reclassify
import numpy as np
import rioxarray
from shapely.geometry import shape
import pygeos
import rasterio
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

    def polygonize(self,da):
        if da.dims != ("y", "x"):
            raise GeoEDFError('Dimensions must be ("y", "x")')

        values = da.values
        transform = da.rio.transform()
        shapes = rasterio.features.shapes(values, transform=transform)

        geometries = []
        col_values = []
        for (geom, col_val) in shapes:
            geometries.append(shape(geom))
            col_values.append(col_val)

        gdf = gpd.GeoDataFrame({"value": col_values, "geometry": geometries}, crs=da.rio.crs)

        return gdf
    
    # each Processor plugin needs to implement this method
    # if error, raise exception
    # assume this method is called only when all params have been fully instantiated
    def process(self):
        
        inundation_map = rioxarray.open_rasterio(self.rasterfile,parse_coordinates=True).squeeze('band', drop=True)
        # Down sampling the inundation map
        rescale_factor = 1 / 5
        new_width = round(inundation_map.rio.width * rescale_factor)
        new_height = round(inundation_map.rio.height * rescale_factor)
        inundation_low_res = inundation_map.rio.reproject(dst_crs=inundation_map.rio.crs,
                                                      shape=(new_height, new_width),
                                                      resampling=rasterio.enums.Resampling.bilinear)

        # Reclassify under-water depth into classes (1: 0-2 feet, 2: 2-6 feet, 3: 6-15 feet, 4: 15 > feet)
        water_lvl = [0, 2, 6, 15, np.inf]  # Original inundation map value (underwater in feet)
        water_lvl_recls = [-9999, 1, 2, 3, 4]

        inundation_recls = reclassify(inundation_low_res, bins=water_lvl, new_values=water_lvl_recls)

        inundation_polygons = self.polygonize(inundation_recls)
        inundation_polygons = inundation_polygons.loc[inundation_polygons['value'] != -9999]

        inundation_per_cls = inundation_polygons.dissolve(by='value')
        inundation_per_cls.reset_index(inplace=True)

        inundation_per_cls.to_file('%s/inundation.shp' % self.target_path)
