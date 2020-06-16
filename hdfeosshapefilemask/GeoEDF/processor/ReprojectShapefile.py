#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
from osgeo import gdal, ogr, osr

from .helper import ProjectionHelper
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Module for reprojecting a shapefile to a desired projection. The desired target 
    projection will be specified either via a local file, or EPSG code, or WKT.
    This module will implement the process() method required for all processors.
"""

class ReprojectShapefile(GeoEDFPlugin):

    # each of the projection input types are optional parameters; however 
    # exactly one of them need to be provided. Desired name for reprojected 
    # shapefile can also be provided
    # in workflow mode, the destination directory will be provided
    # input shapefile is required
    __optional_params = ['prjfile','prjepsg','prjwkt','newname']
    __required_params = ['shapefile']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        # list to hold all param names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for ReprojectShapefile not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        proj_params = ['prjfile','prjepsg','prjwkt']

        # make sure exactly one of the projection params has been provided
        if len(set(kwargs.keys()).intersection(set(proj_params))) != 1:
            raise GeoEDFError('Exactly one among the target projection file, EPSG code, or Well Known Text (WKT) is required')

        # set optional parameters
        for key in self.__optional_params:
            # special error handling of the newname parameter; needs to be a filename
            if key == 'newname':
                val = kwargs.get(key,None)
                if val is not None:
                    if os.path.basename(val) != val:
                        raise GeoEDFError('The value of the newname parameter needs to be a filename and not a path')
                    else:
                        # make sure it has a .shp extension
                        if os.path.splitext(val)[1] != '.shp':
                            raise GeoEDFError('newname must have a .shp extension')
                # set the value
                setattr(self,key,val)
                continue
            
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
        
        super().__init__()


    # the process method that implements the reprojection and save the result to 
    # the target directory. 
    def process(self):
        # set the reprojected file output name and path
        # if a new name has not been provided, reuse the source filename
        # since the output directory is always new, there won't be a clash
        if self.newname is not None:
            outfilename = self.newname
        else:
            (ignore, outfilename) = os.path.split(self.shapefile)

        (outfileshortname, extension) = os.path.splitext(outfilename)
        outfilepath = '%s/%s'% (self.target_path,outfilename)

        driver = ogr.GetDriverByName('ESRI Shapefile')
        indataset = driver.Open(self.shapefile, 0)
        if indataset is None:
            raise GeoEDFError('Error opening shapefile %s in ReprojectShapefile processor' % self.shapefile)
        inlayer = indataset.GetLayer()
        try:
            inSpatialRef = inlayer.GetSpatialRef()
        except:
            raise GeoEDFError('Error determining projection of input shapefile, cannot reproject')

        # construct the desired output projection
        try:
            outSpatialRef = ProjectionHelper.constructSpatialRef(self.prjfile,self.prjepsg,self.prjwkt)
        except BaseException as e:
            raise GeoEDFError('Error occurred when constructing target projection: %s' % e)

        # create Coordinate Transformation
        coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

        # Create the output shapefile
        outdataset = driver.CreateDataSource(outfilepath)
        if outdataset is None:
            raise GeoEDFError('Error creating reprojected shapefile %s', outfile)

        outlayer = outdataset.CreateLayer(outfileshortname, geom_type=inlayer.GetGeomType())

        # add fields
        inLayerDefn = inlayer.GetLayerDefn()
        for i in range(0, inLayerDefn.GetFieldCount()):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            outlayer.CreateField(fieldDefn)
    
        featureDefn = outlayer.GetLayerDefn()
        infeature = inlayer.GetNextFeature()
        while infeature:
            #get the input geometry
            geometry = infeature.GetGeometryRef()
            #reproject the geometry, each one has to be projected seperately
            geometry.Transform(coordTransform)
            #create a new output feature
            outfeature = ogr.Feature(featureDefn)
            #set the geometry and attribute
            outfeature.SetGeometry(geometry)
            #set field values from input shapefile
            #for i in range(0, featureDefn.GetFieldCount()):
            #    outfeature.SetField(featureDefn.GetFieldDefn(i).GetNameRef(), infeature.GetField(i))
            #add the feature to the output shapefile
            outlayer.CreateFeature(outfeature)
            #destroy the features and get the next input features
            outfeature.Destroy
            infeature.Destroy
            infeature = inlayer.GetNextFeature()

        #close the shapefiles
        indataset.Destroy()
        outdataset.Destroy()

        #create the new prj projection file
        outSpatialRef.MorphToESRI()
        outPrjFileName = '%s/%s.prj' % (self.target_path,outfileshortname)
        outPrjFile = open(outPrjFileName,'w')
        outPrjFile.write(outSpatialRef.ExportToWkt())
        outPrjFile.close()        




