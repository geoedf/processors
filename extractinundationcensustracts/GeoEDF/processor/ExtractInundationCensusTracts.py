#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import subprocess
import os
from osgeo import gdal
import requests
import json
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
import pygeos
import pandas as pd

""" Module for implementing the ExtractInundationCensusTracts processor. This accepts a flood inundation map
    GeoTIFF as input and returns a JSON file with the dam ID, scenario ID, GeoID for census tract and a 0 or 1 
    whether this census tract falls within the inundation zone of the map.
"""

class ExtractInundationCensusTracts(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['floodmap_path']
    
    __river_shapefile = '/usr/local/data/HydroRIVERS_v10_na.shp'
    __census_jsonfile = '/usr/local/data/census_tract_from_api.geojson'

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for ExtractInundationCensusTracts not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # class super class init
        super().__init__()
        
    # find the scenario ID given a load, breach condition and dam ID
    def find_scenario_id(self,load_condition,breach_condition,dam_id):
        r = requests.get("https://fim.sec.usace.army.mil/ci/fim/getEAPLayers?id=" + dam_id)
    
        if r.status_code == 200:
            scenarios = json.loads(r.content)
            for scene_num in range(len(scenarios)):
                loadCondition = scenarios[scene_num]['loadCondition']
                breachCondition = scenarios[scene_num]['breachCondition']
                if (loadCondition == load_condition) and (breachCondition == breach_condition):
                    return scene_num
            return np.nan
        else:
            return np.nan        
        
    # reclassify, resample, and polygonize raster flood inundation map
    def polygonize_fim(self,rasterfile):
        # first determine pixel size to resample to 10x
        xres = 0
        yres = 0
        filename = rasterfile.split("/")[-1].split(".")[-2]
        try:
            out = subprocess.run(["gdalinfo","-json",rasterfile],stdout=subprocess.PIPE)
            raster_meta = json.loads(out.stdout.decode('utf-8'))
            if 'geoTransform' in raster_meta:
                xres = raster_meta['geoTransform'][1]
                yres = raster_meta['geoTransform'][5]
                xres = xres * 10
                yres = yres * 10
            else:
                raise GeoEDFError('Error determining pixel size for raster file')
        except:
            raise GeoEDFError('Error determining pixel size for raster file')
            
        if (xres != 0) and (yres != 0):
            # resample raster
            save_path = self.target_path +"/"+ filename + "_resample.tiff"
            subprocess.run(["gdalwarp","-r","bilinear","-of","GTiff","-tr",str(xres),str(yres),rasterfile,save_path])
            
            # now reclassify raster
            water_lvl = [0, 2, 6, 15, np.inf]  # Original inundation map value (underwater in feet)
            water_lvl_recls = [-9999, 1, 2, 3, 4]
            reclass_file = self.target_path + "/" + filename + "_reclass.tiff"
            outfile = "--outfile="+reclass_file
            subprocess.run(["gdal_calc.py","-A",save_path,outfile,"--calc=-9999*(A<=0)+1*((A>0)*(A<=2))+2*((A>2)*(A<=6))+3*((A>6)*(A<=15))+4*(A>15)","--NoDataValue=-9999"],stdout=subprocess.PIPE)
            
            # now polygonize the reclassified raster
            geojson_out = "%s/%s.json" % (self.target_path,filename)
            subprocess.run(["gdal_polygonize.py",reclass_file,geojson_out,"-b","1",filename,"value"])
            
            inundation_polygons = gpd.read_file(geojson_out)
            
            inundation_polygons = inundation_polygons.loc[inundation_polygons['value'] != -9999]  # Remove pixels of null value

            # drop invalid geometries
            inundation_polygons = inundation_polygons.loc[inundation_polygons['geometry'].is_valid, :]
            
            # Entire coverage of inundation map
            inundation_dis_geom = inundation_polygons.geometry.unary_union

            # Coverage for each class of inundation map
            inundation_per_cls = inundation_polygons.dissolve(by='value')
            inundation_per_cls.reset_index(inplace=True)

            # Save the polygonized results
            #poly_out = "%s/%s.geojson" % (self.target_path,filename)
            #inundation_polygons.to_file(poly_out)
            
            # remove all temp files
            os.remove(save_path)
            os.remove(reclass_file)
            os.remove(geojson_out)
            
            return inundation_per_cls, inundation_dis_geom
        else:
            raise GeoEDFError('Resampled raster does not have valid pixel resolution')
            
    def extract_inundated_area_geoid(self, fim_path, dam_id, scene_num):

        # DF preparation for census tracts and rivers
        census_gdf = gpd.read_file(self.__census_jsonfile)

        # Rivers to create benchmark area of each inundated area
        river_gdf = gpd.read_file(self.__river_shapefile)
        river_gdf = river_gdf.to_crs(epsg=4326)
        
        # Destination dataframe to save the results
        inund_area_geoid_df = pd.DataFrame(columns=['Dam_ID', 'Scenario', 'GEOID', 'Class'])

        inund_per_cls_gdf, inund_dis = self.polygonize_fim(fim_path)
        print(f'Completed: Tiff to Polygon conversion for {dam_id}_{scene_num}')
        
        # Create STRtree for census_gdf
        census_geoms = pygeos.from_shapely(census_gdf['geometry'].values)
        census_geoms_tree = pygeos.STRtree(census_geoms, leafsize=50)

        # Extract census tract intersecting with each class of inundation map
        for cls in inund_per_cls_gdf['value'].unique():
            inund_per_cls_geom = pygeos.from_shapely(inund_per_cls_gdf.loc[inund_per_cls_gdf['value'] == cls, 'geometry'].values[0])
            query_inund_census_geom = census_geoms_tree.query(inund_per_cls_geom, predicate='intersects')
            inund_census_gdf = census_gdf.loc[query_inund_census_geom]

            for geoid_ in inund_census_gdf['GEOID'].to_list():
                new_row = pd.DataFrame({'Dam_ID': dam_id, 'Scenario': scene_num, 'GEOID': geoid_, 'Class': cls}, index=[0])
                inund_area_geoid_df = pd.concat([new_row, inund_area_geoid_df]).reset_index(drop=True)
        print(f'Completed: Inundated census tract extraction for {dam_id}_{scene_num}')

        # Create STRtree for rivers_gdf
        river_geoms = pygeos.from_shapely(river_gdf['geometry'].values)
        river_geoms_tree = pygeos.STRtree(river_geoms, leafsize=50)

        # Extract benchmark area (not inundated) intersecting with 10-km buffer around the inundated river
        inund_dis_geom = pygeos.from_shapely(inund_dis)
        query_benchmark_census_geom = river_geoms_tree.query(inund_dis_geom, predicate='intersects')

        inund_river_gdf = river_gdf.loc[query_benchmark_census_geom]
        inund_river_gdf = inund_river_gdf.to_crs(epsg=5070)
        inund_river_gdf['geometry'] = inund_river_gdf['geometry'].buffer(10000) # 10 km buffer around the inundated river
        inund_river_gdf = inund_river_gdf.to_crs(epsg=4326)

        inund_river_geom = pygeos.from_shapely(inund_river_gdf['geometry'].unary_union)
        query_benchmark_census_geom = census_geoms_tree.query(inund_river_geom, predicate='intersects')
        benchmark_census_gdf = census_gdf.loc[query_benchmark_census_geom]

        for geoid_ in benchmark_census_gdf['GEOID'].to_list():
            new_row = pd.DataFrame({'Dam_ID': dam_id, 'Scenario': scene_num, 'GEOID': geoid_, 'Class': 0}, index=[0])
            inund_area_geoid_df = pd.concat([new_row, inund_area_geoid_df]).reset_index(drop=True)
        print(f'Completed: Benchmark area extraction for {dam_id}_{scene_num}')
        
        return inund_area_geoid_df
        
    # each Processor plugin needs to implement this method
    # if error, raise exception
    # assume this method is called only when all params have been fully instantiated
    def process(self):
        
        inundated_census_geoms = pd.DataFrame(columns=['Dam_ID', 'Scenario', 'GEOID', 'Class']) 
        try:
            # find the raster file in the given floodmap_path
            # run this process for every dam inundation map found there
            # destructively update floodmap_path to fully qualified path
            for dir_or_file in os.listdir(self.floodmap_path):
                if dir_or_file.endswith('.tiff'):
                    # found a dam FIM file
                    filename,ext = os.path.splitext(dir_or_file)
                    # now split by _ to determine load, breach and dam ID
                    dam_data = filename.split('_')
                    load_condition = dam_data[0]
                    breach_condition = dam_data[1]
                    dam_id = dam_data[2]
                    
                    # find the scenario ID for this load and breach condition
                    scenario_id = self.find_scenario_id(load_condition,breach_condition,dam_id)
                    
                    # polygonize the raster flood map
                    fim_path = '%s/%s' % (self.floodmap_path,dir_or_file)
                        
                    result = self.extract_inundated_area_geoid(fim_path, dam_id, scenario_id)
                    print("Successfully determine census tracts for dam : ",dam_id)
                    inundated_census_geoms = pd.concat([result, inundated_census_geoms]).reset_index(drop=True)
                    
            result_filename = '%s/census_tracts.csv' % self.target_path
            inundated_census_geoms.to_csv(result_filename,index=False)
            
        except:
            raise GeoEDFError("Error occurred when processing inundation maps for census tracts")
        
