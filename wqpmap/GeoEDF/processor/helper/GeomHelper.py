#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import geopandas as gpd
from shapely.geometry import Polygon

from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Helper module implementing various geometry operations 
"""

def geom_distance(lat1, lon1, lat2, lon2):
    try:
        R = 6378.137 # Radius of earth in KM
        dLat = lat2 * math.pi / 180 - lat1 * math.pi / 180
        dLon = lon2 * math.pi / 180 - lon1 * math.pi / 180
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c
    except:
        raise GeoEDFError('Could not determine geometry distance')

    return d # Km

def geom_diagonal(geom):
    try:
        lon1 = geom.total_bounds[0]
        lat1 = geom.total_bounds[1]
        lon2 = geom.total_bounds[2]
        lat2 = geom.total_bounds[3]
        d = geom_distance(lat1, lon1, lat2, lon2)
    except:
        raise GeoEDFError('Could not determine geometry diagonal')

    return d # Km

def geom_extent(geom):
    try:
        d2 = geom_width(geom)+geom_height(geom)
    except:
        raise GeoEDFError('Could not determine geometry extent')

    return d2 # Km

def geom_height(geom):
    try:
        lon1 = geom.total_bounds[0]
        lat1 = geom.total_bounds[1]
        lon2 = geom.total_bounds[2]
        lat2 = geom.total_bounds[3]
        h = geom_distance(lat1, lon1, lat2, lon1)
    except:
        raise GeoEDFError('Could not determine geometry height')

    return h # Km

def geom_width(geom):
    try:
        lon1 = geom.total_bounds[0]
        lat1 = geom.total_bounds[1]
        lon2 = geom.total_bounds[2]
        lat2 = geom.total_bounds[3]
        w = geom_distance(lat1, lon1, lat1, lon2)
    except:
        raise GeoEDFError('Could not determine geometry width')

    return w # Km

def geom_bbox(geom):
    try:
        polygon = gpd.GeoDataFrame(gpd.GeoSeries(geom.envelope), columns=['geometry'])
    except:
        raise GeoEDFError('Could not determine geometry bbox')

    return polygon

# In case CRS is different
def geom_bbox2(geom):
    try:
        lon_point_list = [geom.total_bounds[0],geom.total_bounds[2],geom.total_bounds[2],geom.total_bounds[0],geom.total_bounds[0]]
        lat_point_list = [geom.total_bounds[1],geom.total_bounds[1],geom.total_bounds[3],geom.total_bounds[3],geom.total_bounds[1]]
        polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
        crs = {'init': 'epsg:4326'}
        polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])    
    except:
        raise GeoEDFError('Could not determine geometry bbox2')

    return polygon

# Try using the area of the total_bounds polygon in both degrees and meters to generate an approximate "conversion" factor
def geom_area(geom):
    try:
        factor = geom_width(geom)*geom_height(geom)/geom_bbox(geom).area
        area = factor*geom.area
    except:
        raise GeoEDFError('Could not determine geometry area')
    
    return area # Km^2

# Use a cartesian projection coordinate system to get true area
    # *** Currently crashes kernel ***
def geom_area2(geom):
    try:
        geom_m = geom.to_crs(epsg=3857) # or 3395 (WGS 84 compliant)
        # May need to use explicit definition for 3395: 
        #   proj4.defs("EPSG:3395","+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")
        a = geom_m.area/10**6
    except:
        raise GeoEDFError('Could not determine geometry area2')

    return a # Km^2
