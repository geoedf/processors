MergeArcGridRasters
====================

.. py:class:: GeoEDF.processor.MergeArcGridRasters()

   Module for merging a directory of rasters which are in the ArcGrid format
   The QGIS gdal:merge processor is used to merge the given rasters
   Given a directory input, the subdirectories with names beginning in "grd"
   are assumed to hold an ArcGrid raster file and used as the input list of 
   raster to merge

   .. py:attribute:: input_folder (str,required)

   The path to the folder must be specified, which cotnains the rasters.



