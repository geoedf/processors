PickleGHCNDData
====================

.. py:class:: GeoEDF.processor.PickleGHCNDData()

   Module for implementing the processor for creating a pickle file from rolling 7 and 30-day windows of 
   per-parameter GHCND data. This plugin assumes the files are named <param>.csv. This plugin will process 
   a directory containing these per-parameter CSV files. It creates one pickle file per parameter. 

   .. py:attribute:: data_dir (str,required)

   The path to the folder must be specified, which contains the HDF files.


