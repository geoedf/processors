PolygonizeDamFIM
====================

.. py:class:: GeoEDF.processor.PolygonizeDamFIM()

   Module for implementing the PolygonizeDamFIM processor. This accepts a flood inundation map
   GeoTIFF as input and returns a shapefile that has been reclassified and reduced in scale.

   .. py:attribute:: rasterfile (str,required)

   Path to the flood inundation map, which is a GeoTIFF.
