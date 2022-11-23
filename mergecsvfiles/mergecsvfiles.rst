Merge CSV Files Processor
=================================

.. py:class:: GeoEDF.processor.MergeCSVFiles()

   Processor plugin that takes a directory of CSV files and merges them into a single CSV file. 
   An optional basename can be provided for the resulting CSV file.

   .. py:attribute:: filepath (str,required)

   This is the directory where the CSV files to be merged are located.

   .. py:attribute:: basename (str,optional)
   
   If specified the merged CSV file would have the name as specified by this parameter.
