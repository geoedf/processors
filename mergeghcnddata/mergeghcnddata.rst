MergeGHCNDData
====================

.. py:class:: GeoEDF.processor.MergeGHCNDData()

    Module for implementing the processor for merging per-station GHCND data. This plugin will process 
    a directory containing per-station,per-parameter CSV files. It merges the data, producing a single CSV
    file for each parameter. Each column in this result CSV corresponds to a station.

   .. py:attribute:: data_dir (str,required)

  The path to the folder must be specified, which contains the CSV files.

