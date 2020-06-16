#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from osgeo import gdal, ogr, osr

from .helper import HDFEOSHelper
from GeoEDF.processor.ReprojectShapefile import ReprojectShapefile
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Module for aggregating the data values from a HDF file for a given shapefile
    containing polygons. This supports both HDF4 and HDF5, but assumes that the files 
    are in the HDF-EOS format. All processing occurs in the latitude-longitude space
    by reprojecting the shapefile to WGS84 and extracting the lat-lon for each grid cell 
    in the HDF file. Extraction of cell lat-lon pairs for HDF4 files relies on the 
    eos2dump utility. This supports aggregating more than one subdataset from a HDF file;
    the resulting shapefile contains a separate field for each subdataset aggregate value.
"""

class HDFEOSShapefileMask(GeoEDFPlugin):

    # in workflow mode, the destination directory will be provided
    # input hdf and shapefiles are required
    # list of HD subdatasets to be processed is also required
    # only a distinguishing substring of the subdataset name is required
    __optional_params = []
    __required_params = ['hdffile','shapefile','datasets']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for HDFEOSShapefileMask not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        super().__init__()

    # the process method that performs the masking and aggregating operation and saves resulting 
    # shapefile to the target directory. 
    def process(self):
        
        # first reproject the shapefile to WGS84; all processing will happen in lat-lon
        # use the ReprojectShapefile processor

        # Set the name of this new shapefile based on the HDF filename
        (ignore, hdffilename) = os.path.split(self.hdffile)
        tmpfilename = '%s.shp' % hdffilename

        # reproject shapefile
        try:
            # first get the HDF file's native projection
            #hdf_proj_wkt = HDFEOSHelper.HDF_proj_WKT(self.hdffile)
            shapefileReprojector = ReprojectShapefile(shapefile=self.shapefile,prjepsg='4326',newname=tmpfilename)
            shapefileReprojector.target_path = self.target_path
            #shapefileReprojector = ReprojectShapefile(shapefile=self.shapefile,destdir=self.destdir,prjwkt=hdf_proj_wkt,newname=tmpfilename)
            shapefileReprojector.process()
            shapefile_wgs84 = '%s/%s' % (self.target_path,tmpfilename)
        except:
            raise GeoEDFError('Error reprojecting input shapefile, cannot proceed with masking HDF data')

        # now process the HDF file's subdatasets 
        # get the data matrix for the selected subdatasets
        hdf_data = HDFEOSHelper.HDF_subdataset_data(self.hdffile,self.datasets)

        # get the lat-lon for the corner coordinates
        #(upperLeftX, upperLeftY, lowerRightX, lowerRightY) = HDFEOSHelper.HDF_corner_coords(self.hdffile)
        (upperLeftX, upperLeftY, lowerRightX, lowerRightY) = (-180,90,180,-90)

        # get the grid dimensions of the data
        hdf_sample_data = next(iter(hdf_data.values()))['data']
        num_rows = hdf_sample_data.shape[0]
        num_cols = hdf_sample_data.shape[1]

        #print(num_rows,num_cols)

        # determine area of a single grid cell; assume equal size grids
        grid_cell_width = (lowerRightX-upperLeftX)/num_cols
        grid_cell_height = (upperLeftY-lowerRightY)/num_rows
        grid_cell_rect = ogr.Geometry(ogr.wkbLinearRing)
        grid_cell_rect.AddPoint(upperLeftX, upperLeftY)
        grid_cell_rect.AddPoint(upperLeftX+grid_cell_width, upperLeftY)
        grid_cell_rect.AddPoint(upperLeftX+grid_cell_width, upperLeftY-grid_cell_height)
        grid_cell_rect.AddPoint(upperLeftX, upperLeftY-grid_cell_height)
        grid_cell_rect.AddPoint(upperLeftX, upperLeftY)
        grid_cell_geom = ogr.Geometry(ogr.wkbPolygon)
        grid_cell_geom.AddGeometry(grid_cell_rect)
        grid_cell_area = grid_cell_geom.Area()

        shp_driver = ogr.GetDriverByName("ESRI Shapefile")
        mask_shp_data_source = shp_driver.Open(shapefile_wgs84, 1)
        mask_shp_layer = mask_shp_data_source.GetLayer()
        #print(mask_shp_layer.GetExtent())

        # add new fields to store the aggregate value for each subdataset
        for key in hdf_data.keys():
            # dbfs only allow for field names up to 10 characters long
            key_10char = key[0:10]
            mask_shp_layer.CreateField(ogr.FieldDefn(key_10char, ogr.OFTReal))

        # loop through shapefile features, determining different subdataset aggregate value for each
        for ignore, mask_shp_feature in enumerate(mask_shp_layer):
            mask_shp_feature_geom = mask_shp_feature.GetGeometryRef()
            mask_shp_feature_area = mask_shp_feature_geom.Area()

            # initialize dictionary of aggregate data for each hdf subdataset for the current feature
            feature_hdf_data = dict()
            for key in hdf_data.keys():
                feature_hdf_data[key] = 0.0

            # factor to weigh aggregate data by based on intersection areas with each grid cell
            feature_weight = 0.0

            # get the bounds of the feature
            mask_shp_feature_geom.FlattenTo2D()
            x_min, x_max, y_min, y_max = mask_shp_feature_geom.GetEnvelope()

            # optimization to only process intersecting rows and columns rather than all grids
            j_low = max(0, int((x_min - upperLeftX)/grid_cell_width) - 1)
            j_high = min(num_cols, int((x_max - upperLeftX)/grid_cell_width) + 1)
            i_low = max(0, int((upperLeftY - y_max)/grid_cell_height) - 1)
            i_high = min(num_rows, int((upperLeftY - y_min)/grid_cell_height) + 1)

            num_cells = 0
            num_cells_0 = 0
            num_cells_1 = 0
            num_cells_partial = 0

            # loop through grid cells, checking for intersection with feature and aggregating 
            # weighted value for each subdataset
            for i in range(i_low,i_high):
                # further optimize by determining the subset of columns that are relevant for this row
                row_rect = ogr.Geometry(ogr.wkbLinearRing)
                row_rect.AddPoint(upperLeftX+j_low*grid_cell_width, upperLeftY-i*grid_cell_height)
                row_rect.AddPoint(upperLeftX+(j_high+1)*grid_cell_width, upperLeftY-i*grid_cell_height)
                row_rect.AddPoint(upperLeftX+(j_high+1)*grid_cell_width, upperLeftY-(i+1)*grid_cell_height)
                row_rect.AddPoint(upperLeftX+j_low*grid_cell_width, upperLeftY-(i+1)*grid_cell_height)
                row_rect.AddPoint(upperLeftX+j_low*grid_cell_width, upperLeftY-i*grid_cell_height)
                row_geom = ogr.Geometry(ogr.wkbPolygon)
                row_geom.AddGeometry(row_rect)

                row_intersection_geom = row_geom.Intersection(mask_shp_feature_geom)
                row_intersection_area = row_intersection_geom.Area()
                if row_intersection_geom != None and row_intersection_area > 0.0:
                    row_x_min, row_x_max, row_y_min, row_y_max = row_intersection_geom.GetEnvelope()
                    new_j_low = max(0, int((row_x_min - upperLeftX)/grid_cell_width) - 1)
                    new_j_high = min(num_cols, int((row_x_max - upperLeftX)/grid_cell_width) + 1)
                else:
                    row_intersection_geom = mask_shp_feature_geom
                    new_j_low = j_low
                    new_j_high = j_high

                for j in range(new_j_low,new_j_high):

                    num_cells = num_cells + 1

                    # get the cell value
                    cell_val = hdf_data[key]['data'][i][j]

                    # TODO: move this out of the loop
                    # if this cell doesn't contain a valid value, skip
                    if False and 'range' in hdf_data[key]:
                        val_range = hdf_data[key]['range']
                        if not (val_range[0] < cell_val < val_range[1]):
                            continue
                    else: # skip cells that contain the "nodata" value
                        if 'fillValue' in hdf_data[key]:
                            fillValue = hdf_data[key]['fillValue']
                            if cell_val == fillValue or cell_val == 0 - fillValue:
                                continue

                    # construct a grid cell based on the lat-lon values for this grid row and column
                    cell_rect = ogr.Geometry(ogr.wkbLinearRing)
                    cell_rect.AddPoint(upperLeftX+j*grid_cell_width, upperLeftY-i*grid_cell_height)
                    cell_rect.AddPoint(upperLeftX+(j+1)*grid_cell_width, upperLeftY-i*grid_cell_height)
                    cell_rect.AddPoint(upperLeftX+(j+1)*grid_cell_width, upperLeftY-(i+1)*grid_cell_height)
                    cell_rect.AddPoint(upperLeftX+j*grid_cell_width, upperLeftY-(i+1)*grid_cell_height)
                    cell_rect.AddPoint(upperLeftX+j*grid_cell_width, upperLeftY-i*grid_cell_height)
                    cell_geom = ogr.Geometry(ogr.wkbPolygon)
                    cell_geom.AddGeometry(cell_rect)

                    # check to see if the grid cell intersects the column intersection geometry
                    # get the overlap area to weight the aggregation calculation
                    if (cell_geom.Disjoint(row_intersection_geom)): # the geometries are disjoint
                        num_cells_0 = num_cells_0 + 1
                        cell_intersection_area = 0.0
                    elif (cell_geom.Within(row_intersection_geom)): # grid cell is fully contained
                        num_cells_1 = num_cells_1 + 1
                        cell_intersection_area = grid_cell_area
                    else:
                        num_cells_partial = num_cells_partial + 1
                        cell_intersection_geom = cell_geom.Intersection(row_intersection_geom) # grid cell intersects feature
                        if (cell_intersection_geom != None):
                            cell_intersection_area = cell_intersection_geom.Area()
                        else:
                            cell_intersection_area = 0.0

                    # grid cell does not intersect the feature
                    if (cell_intersection_area <= 0.0):
                        continue

                    # add the weighted contribution of this grid cell to the feature value for each subdataset
                    for key in hdf_data.keys():
                        feature_hdf_data[key] += hdf_data[key]['data'][i][j]*cell_intersection_area/grid_cell_area

                    feature_weight += cell_intersection_area/grid_cell_area

            # done with loop over grid cells, compute actual weighted aggregate value for feature
            for key in hdf_data.keys():
                key_10char = key[0:10]
                if feature_weight > 0.0:
                    feature_hdf_data[key] = feature_hdf_data[key]/feature_weight
                else:
                    feature_hdf_data[key] = 0.0

                # set the value for this subdataset field on the feature
                mask_shp_feature.SetField(key_10char,feature_hdf_data[key])
                mask_shp_layer.SetFeature(mask_shp_feature)
                mask_shp_data_source.SyncToDisk()

        # close the result shapefile
        mask_shp_layer = None
        mask_shp_data_source.SyncToDisk()
        mask_shp_data_source = None



                    


                    

            
            

        






