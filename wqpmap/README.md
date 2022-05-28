# WQP Map
WQPMap is a GeoEDF Processor plugin to extract hygrologic and water quality data from USGS, EPA and other resources and creates a interactive map in standalone HTML and JavaScript.  The data is associated with a stream reach containing a specified USGS (NWIS) gage station and an upstream/downstream range.  This includes data from the Water Quality Portal (WQP) for WQP stations along the stream reach. The data can also be restricted to a give date range.  The hydrologic data includes various HUCs and drainage basins for the target stream reach based on HUC12 pour points, plus upstream tributaries.  The map is generated using the Folium Python package, which is a wrapper for LeafletJS.