#!/usr/bin/env python
# -*- coding: utf-8 -*-

from osgeo import osr

from geoedfframework.utils.GeoEDFError import GeoEDFError


""" Helper module for constructing a spatial reference (aka Projection object)
    from either a prj file, EPSG code, or Well Known Text(WKT). It is assumed 
    that exactly one of these has been provided
"""

def constructSpatialRef(prj_file=None,prj_epsg_code=None,prj_wkt=None):

    try:
        outSpatialRef = osr.SpatialReference()
        # if projection file provided, read the WKT
        if prj_file is not None:
            prjfile = open(prj_file, 'r')
            prj_txt = prjfile.read()
            outSpatialRef.ImportFromESRI([prj_txt])
        elif prj_epsg_code is not None:
            if prj_epsg_code.isdigit():
                outSpatialRef.ImportFromEPSG(int(prj_epsg_code))
        elif prj_wkt is not None:
            outSpatialRef.ImportFromESRI([prj_wkt])
        else:
            raise GeoEDFError('Non-null target projection file, EPSG code, or WKT is required')
        return outSpatialRef
    except:
        raise
