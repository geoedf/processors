SubsetAORCForcingData
====================

.. py:class:: GeoEDF.processor.SubsetAORCForcingData()

   Module for implementing the SubsetAORCForcingData processor. The processor takes a 
   start and end date as well as a HUC12 ID or shapefile or geospatial extents as input. 
   AORC data is clipped to the provided extent and the necessary forcing data input variables 
   are extracted. A path to pre-downloaded AORC data files is required.

   .. py:attribute:: start_date (str,required)

   Start date in the format, '%m/%d/%Y'.

   .. py:attribute:: end_date (str,required)

   End date in the format, '%m/%d/%Y'.

   .. py:attribute:: aorc_datapath (list,required)

   This is a list of one or more names of subdatasets that need to be aggregated.

   .. py:attribute:: huc12_id (str,optional)

   If shapefile is not specified, then the HUC12 id is used. 

   .. py:attribute:: shapefile (str,optional)

   This needs to be a local file path to a ``.shp`` shapefile.

   .. py:attribute:: extents (list,optional)

   This is the list of extents in the order, xmin, xmax, ymin, ymax.

