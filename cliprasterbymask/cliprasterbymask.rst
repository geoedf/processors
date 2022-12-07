ClipRasterByMask
====================

.. py:class:: GeoEDF.processor.ClipRasterByMask()

    Module for clipping a raster to the extents of a given mask layer as a Shapefile.
    The two files may be in different projections; here we reproject to the mask layer's
    projection. The raster can be in any standard raster format

   .. py:attribute:: raster_file (str,required)

   Only a directory/folder of rasters is required.
  
   .. py:attribute:: mask_shapefile (str,required)

   Path to the mask shapefile to be projected to. 

