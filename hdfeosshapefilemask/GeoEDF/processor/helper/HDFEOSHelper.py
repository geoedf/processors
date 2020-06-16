#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from osgeo import gdal, ogr, osr
from pyhdf.SD import SD, SDC
import h5py
import pyproj

import os
import re

from geoedfframework.utils.GeoEDFError import GeoEDFError


""" Helper module implementing various processing operations 
    on HDF4 and HDF5 files
"""

def HDF_type(hdf_filepath):

    # determine if HDF4 or HDF5 (for now based on file extension alone)
    try:
        (ignore, hdf_filename) = os.path.split(hdf_filepath)
        (ignore, extension) = os.path.splitext(hdf_filename)
        if extension == '.hdf':
            hdftype = 'hdf4'
        elif extension == '.h5':
            hdftype = 'hdf5'
        else:
            raise GeoEDFError('Could not determine HDF file type from file extension')
    except:
        raise GeoEDFError('Could not determine HDF file type')

    return hdftype

def HDF_subdataset_data(hdf_filepath,subdataset_substrs):

    # process the names of the subdatasets, finding any that contain a member of 
    # subdataset_substrs as a substring
    # subdataset_substrs is a list

    # returned dictionary indexed by subdataset name
    # contains data grid and value range
    hdf_data = dict()

    # first determine the HDF type 
    hdf_type = HDF_type(hdf_filepath)

    if hdf_type == 'hdf4':
        hdf_file = SD(hdf_filepath, SDC.READ)
        try:
            dset_names = hdf_file.datasets().keys()
            # loop through input subdataset substrings
            for subdset_substr in subdataset_substrs:
                # loop through datasets in HDF file
                for dset_name in dset_names:
                    # if substring found
                    if subdset_substr in dset_name:
                        # if this subdataset has not been processed before
                        if dset_name not in hdf_data:
                            try:
                                data2D = hdf_file.select(dset_name)
                                data = data2D[:,:].astype(np.float64)
                                hdf_data[dset_name] = dict()
                                hdf_data[dset_name]['data'] = data
                                #hdf_data[dset_name]['range'] = data2D.getrange()
                                hdf_data[dset_name]['fillValue'] = data2D.getfillvalue()
                            except:
                                raise GeoEDFError('Error retrieving subdataset %s data from HDF file' % dset_name)
        except:
            raise GeoEDFError('Error retrieving subdatasets from HDF4 file %s' % hdf_filepath)
    else:
        hdf_file = h5py.File(hdf_filepath, mode='r')
        # assume this follows the structure of HDF-EOS files where all subdatasets are in a "Geophysical_Data" group
        if 'Geophysical_Data' in hdf_file.keys():
            dset_names = hdf_file['Geophysical_Data'].keys()
            # loop through input subdataset substrings
            for subdset_substr in subdataset_substrs:
                # loop through subdatasets in HDF file
                for dset_name in dset_names:
                    # if substring matches
                    if subdset_substr in dset_name:
                        # if subdataset not processed yet
                        if dset_name not in hdf_data:
                            try:
                                # construct fully qualified subdataset name
                                fq_dset_name = '/Geophysical_Data/%s' % dset_name
                                data = hdf_file[fq_dset_name]
                                hdf_data[dset_name] = dict()
                                hdf_data[dset_name]['data'] = data[:]
                                hdf_data[dset_name]['fillValue'] = data.fillvalue
                            except:
                                raise GeoEDFError('Error retrieving subdataset %s data from HDF file' % dset_name)
        else:
            raise GeoEDFError('Cannot handle HDF5 files that do not follow the HDF-EOS standards')

    return hdf_data

def HDF_proj_WKT(hdf_filepath):
    # returns the projection of the HDF file in Well Known Text (WKT) format

    # first determine the HDF type 
    hdf_type = HDF_type(hdf_filepath)
    
    if hdf_type == 'hdf4':
        # for HDF4 assume corner coordinates are stored in the StructMetadata.0 section
        hdf_file = SD(hdf_filepath, SDC.READ)

        try:
            # access grid metadata section of StructMetadata.0
            fattr = hdf_file.attributes(full=1)
            structmeta = fattr['StructMetadata.0']
            gridmeta = structmeta[0]

            # determine the projection GCTP code from the grid metadata
            proj_regex = re.compile(r'''Projection=(?P<projection>\w+)''',re.VERBOSE)
            match = proj_regex.search(gridmeta)
            proj = match.group('projection')

            # support MODIS sinusoidal projection for now, add others later
            if proj == 'GCTP_SNSOID':
                sinu_proj4 = "+proj=sinu +R=6371007.181 +nadgrids=@null +wktext"
                srs = osr.SpatialReference()
                srs.ImportFromProj4(sinu_proj4)
                return srs.ExportToWkt()
        except:
            #prjfile = open('/home/rkalyana/GeoEDF/GeoEDF/connector/filter/modis/6933.prj', 'r')
            #prj_txt = prjfile.read()
            #srs = osr.SpatialReference()
            #srs.ImportFromESRI([prj_txt])
            #prjfile.close()
            #return srs.ExportToWkt()
            raise GeoEDFError('Error determining the projection or unsupported projection')
    
    else: # HDF5 file; only SMAP files in EASE Grid 2.0 are supported at the moment
        hdf_file = h5py.File(hdf_filepath, mode='r')

        # check to see if this is a EASE Grid 2.0 file
        if 'EASE2_global_projection' in hdf_file.keys():
            ease_proj4 = "+proj=cea +lat_0=0 +lon_0=0 +lat_ts=30 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m"
            srs = osr.SpatialReference()
            srs.ImportFromProj4(ease_proj4)
            return srs.ExportToWkt()
        else:
            raise GeoEDFError('Error determining the projection or unsupported projection')

def HDF_corner_coords(hdf_filepath):

    # return a tuple of upper left and lower right coordinates in lat-lon

    # first determine the HDF type 
    hdf_type = HDF_type(hdf_filepath)
    
    if hdf_type == 'hdf4':
        # for HDF4 assume corner coordinates are stored in the StructMetadata.0 section
        hdf_file = SD(hdf_filepath, SDC.READ)

        try:
            # access grid metadata section of StructMetadata.0
            fattr = hdf_file.attributes(full=1)
            structmeta = fattr['StructMetadata.0']
            gridmeta = structmeta[0]
        
            # parse the text to retrieve corner coordinates in meters
            ul_regex = re.compile(r'''UpperLeftPointMtrs=\(
                                  (?P<upper_left_x>[+-]?\d+\.\d+)
                                  ,
                                  (?P<upper_left_y>[+-]?\d+\.\d+)
                                  \)''', re.VERBOSE)
            match = ul_regex.search(gridmeta)
            x0 = np.float(match.group('upper_left_x')) 
            y0 = np.float(match.group('upper_left_y')) 

            lr_regex = re.compile(r'''LowerRightMtrs=\(
                                  (?P<lower_right_x>[+-]?\d+\.\d+)
                                  ,
                                  (?P<lower_right_y>[+-]?\d+\.\d+)
                                  \)''', re.VERBOSE)
            match = lr_regex.search(gridmeta)
            x1 = np.float(match.group('lower_right_x')) 
            y1 = np.float(match.group('lower_right_y')) 

            # construct the projection transformer to convert from meters to lat-lon

            # determine the projection GCTP code from the grid metadata
            proj_regex = re.compile(r'''Projection=(?P<projection>\w+)''',re.VERBOSE)
            match = proj_regex.search(gridmeta)
            proj = match.group('projection')

            # support MODIS sinusoidal projection for now, add others later
            if proj == 'GCTP_SNSOID':
                #sinu = pyproj.Proj("+proj=sinu +R=6371007.181 +nadgrids=@null +wktext")
                #wgs84 = pyproj.Proj("+init=EPSG:4326")
                #lon0, lat0 = pyproj.transform(sinu, wgs84, x0, y0)
                #lon1, lat1 = pyproj.transform(sinu, wgs84, x1, y1)

                #return (lon0, lat0, lon1, lat1)
                return (x0, y0, x1, y1)

            else:
                raise GeoEDFError('Only MODIS sinusoidal grids are supported currently')

        except Exception as e:
            #x0, y0, x1, y1 = -17357881.81713629,7324184.56362408,17357881.81713629,-7324184.56362408
            #return (x0,y0,x1,y1)
            raise GeoEDFError('Error retrieving corner coordinates of HDF file')

    else: # HDF5 file; only SMAP files in EASE Grid 2.0 are supported at the moment
        hdf_file = h5py.File(hdf_filepath, mode='r')

        # check to see if this is a EASE Grid 2.0 file
        if 'EASE2_global_projection' in hdf_file.keys():
            # hardcoded corner coordinates, since this is not stored in the file metadata
            x0, y0, x1, y1 = -17357881.81713629,7324184.56362408,17357881.81713629,-7324184.56362408

            #ease = pyproj.Proj(("+proj=cea +lat_0=0 +lon_0=0 +lat_ts=30 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m"))
            #wgs84 = pyproj.Proj("+init=EPSG:4326")
            #lon0, lat0 = pyproj.transform(ease, wgs84, x0, y0)
            #lon1, lat1 = pyproj.transform(ease, wgs84, x1, y1)

            #return (lon0, lat0, lon1, lat1)
            return (x0, y0, x1, y1)

        else:
            raise GeoEDFError('Only EASE Grid 2.0 HDF5 files are supported currently')


