Shapefile2GeoJSON
====================

.. py:class:: GeoEDF.processor.Shapefile2GeoJSON()

   Module for implementing the Shapefile2GeoJSON processor. This supports both a directory 
   of shapefiles (as a step in a workflow) and a single shapefile (when working on a locally 
   uploaded file). The resulting GeoJSON can be used in various map visualization libraries 
   like Folium or ipyLeaflet.

   .. py:attribute:: inputdir (str,required)

   This is directory for multiple shapefiles.

   .. py:attribute:: shapefile (str,required)

   This needs to be a local file path to a ``.shp`` shapefile. This take precedence over the inputdir. 
