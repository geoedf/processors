#!/usr/bin/env python3

from datetime import datetime

from geoedfframework.GeoEDFPlugin import GeoEDFPlugin
from geoedfframework.utils.GeoEDFError import GeoEDFError
from .helper import GeomHelper, ColorHelper


"""Module to create map of a stream reach based on a specified NWIS (USGS) site and range (up/down stream), 
    including various feature layers derived from USGS NLDI navigation along the stream, 
    its tributaries and associated drainage basins, while also extracting data for further visualization.
    Input parameter include:
        nwis_site ['USGS-03206000']
        um_dist [50]
        dm_dist [25]
        begin_date = [1/1/xx, where xx is 3 years past]
        end_date = [today]
        ignore_wqp_dates [True, all dates]
"""

class WQPMap(GeoEDFPlugin):

    # required inputs are:
    # (1) NWIS (USGS) Station

    # optional inputs can override the region, crop, and livestock sets

    __required_params = ['nwis_site']

    __optional_params = ['um_dist','dm_dist','begin_date','end_date','ignore_wqp_dates']

    # we use just kwargs since this makes it easier to instantiate the object from the 
    # GeoEDFProcessor class
    def __init__(self, **kwargs):

        #list to hold all parameter names
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
               raise GeoEDFError('Required parameter %s for SimpleDataClean not provided' % param)
           
        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            if key == 'um_dist':
                val = kwargs.get(key,50)
                setattr(self,key,val)
                continue
            if key == 'dm_dist':
                val = kwargs.get(key,25)
                setattr(self,key,val)
                continue
            if key == 'begin_date':
                val = kwargs.get(key,None)
                if val is not None:
                    val = datetime.strptime(val,"%m/%d/%Y")
                else:
                    val = kwargs.get(key,datetime(datetime.now().year-3, 1, 1))
                setattr(self,key,val)
                continue
            if key == 'end_date':
                val = kwargs.get(key,None)
                if val is not None:
                    val = datetime.strptime(val,"%m/%d/%Y")
                else:
                    val = datetime.now()
                setattr(self,key,val)
                continue
            if key == 'ignore_wqp_dates':
                val = kwargs.get(key,True)
                setattr(self,key,val)
                continue

            #if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # super class init
        super().__init__()

    # The process method that generates the map
    def process(self):

        # Get things set up
        from os import path

        # Enable numerical arrays and matrices with NumPy
        import numpy as np

        # Enable R-style DataFrames with Pandas
        import pandas as pd

        # Enable Math functions
        import math

        # Enable working with Dates and Times
        from datetime import datetime

        # Enable geospatial DataFrames with GeoPandas (built on Fiona, which is built on GDAL/OGR)
        import geopandas as gpd

        # Enable other geospatial functions using Shapely
        from shapely.geometry import Point, Polygon

        # Enable Leatlet.JS-based mapping with Folium 
        import folium
        from folium import IFrame
        import folium.plugins as plugins

        # Enable HTTP requests and parsing of JSON results
        import requests
        import json

        # Set parameters

        NWIS_SITE = self.nwis_site
        UM_DIST = self.um_dist
        DM_DIST = self.dm_dist
        BEGIN_DATE = "{0:02d}-{1:02d}-{2:4d}".format(self.begin_date.month,self.begin_date.day,self.begin_date.year)
        END_DATE = "{0:02d}-{1:02d}-{2:4d}".format(self.end_date.month,self.end_date.day,self.end_date.year)
        IGNORE_WQP_DATES = self.ignore_wqp_dates

        # URLs for REST Web Services
        USGS_NLDI_WS = "https://labs.waterdata.usgs.gov/api/nldi/linked-data" # USGS NLDI REST web services
        NWIS_SITE_URL = USGS_NLDI_WS+"/nwissite/"+NWIS_SITE 
        NWIS_SITE_NAV = NWIS_SITE_URL+"/navigate"
        TNM_WS = "https://hydro.nationalmap.gov/arcgis/rest/services" # The National Map REST web services
        ARCGIS_WS = "http://server.arcgisonline.com/arcgis/rest/services" # ARCGIS Online REST web services

        # Set Input (optional) and Output Directories
        IN_DIR = "data/"+NWIS_SITE
        OUT_DIR = IN_DIR+"/out"

        # Create output directory if it does not already exist
        #get_ipython().run_line_magic('mkdir', '-p {OUT_DIR}')
        
        try:
            # Get Lat/Lon coordinates of starting site (NWIS station)
            nwis_site_json = gpd.read_file(NWIS_SITE_URL)
            nwis_site_geom = nwis_site_json.iloc[0]['geometry']
            nwis_site_coord = [nwis_site_geom.y, nwis_site_geom.x]

            # Generate map

            river_map = folium.Map(nwis_site_coord,zoom_start=10,tiles=None)
            plugins.ScrollZoomToggler().add_to(river_map);
            plugins.Fullscreen(
                position='bottomright',
                title='Full Screen',
                title_cancel='Exit Full Screen',
                force_separate_button=True
            ).add_to(river_map);

            # Add sites within reach using NLDI web services at USGS

            # Popup parameters
            width = 500
            height = 120
            max_width = 1000

            # Main Stream

            folium.GeoJson(NWIS_SITE_NAV+"/UM?distance="+str(UM_DIST),name="Main Stream (up)",show=True,control=False).add_to(river_map);
            folium.GeoJson(NWIS_SITE_NAV+"/DM?distance="+str(DM_DIST),name="Main Stream (down)",show=True,control=False).add_to(river_map);

            # NWIS Sites

            fg_nwis = folium.FeatureGroup(name="USGS (NWIS) Sites",overlay=True,show=False)
            color = 'darkred'
            icon = 'dashboard'
                    
            nwis_sites_dm = gpd.read_file(NWIS_SITE_NAV+"/DM/nwissite?distance="+str(DM_DIST))
            nwis_sites_um = gpd.read_file(NWIS_SITE_NAV+"/UM/nwissite?distance="+str(UM_DIST))
            nwis_sites = gpd.GeoDataFrame(pd.concat([nwis_sites_dm,nwis_sites_um], ignore_index=True), crs=nwis_sites_dm.crs) # TODO: eliminate duplicate for anchor site

            for i, nwis_site in nwis_sites.iterrows():
                coord = [nwis_site.geometry.y,nwis_site.geometry.x]
                label = 'NWIS Station: '+nwis_site.identifier
                html = label
                html += '<br>{0:s}'.format(nwis_site['name'])
                html += '<br><a href=\"{0:s}\" target=\"_blank\">{1:s}</a>'.format(nwis_site.uri+'/#parameterCode=00065&startDT='+BEGIN_DATE+'&endDT='+END_DATE,nwis_site.uri)
                html += '<br>Lat: {0:.4f}, Lon: {1:.4f}'.format(nwis_site.geometry.y,nwis_site.geometry.x)
                html += '<br>Comid: {0:s}'.format(nwis_site.comid)
                iframe = folium.IFrame(html,width=width,height=height)
                popup = folium.Popup(iframe,max_width=max_width)
                fg_nwis.add_child(folium.Marker(location=coord,icon=folium.Icon(color=color,icon=icon),popup=popup,tooltip=label));
                    
            fg_nwis.add_to(river_map)

            # WQP Stations

            fg_wqp = folium.FeatureGroup(name="WQP Stations",overlay=True,show=False)
            color = 'darkgreen'
            radius = 3
                    
            wqp_sites_dm = gpd.read_file(NWIS_SITE_NAV+"/DM/wqp?distance="+str(DM_DIST))
            wqp_sites_um = gpd.read_file(NWIS_SITE_NAV+"/UM/wqp?distance="+str(UM_DIST))
            wqp_sites = gpd.GeoDataFrame(pd.concat([wqp_sites_dm,wqp_sites_um], ignore_index=True), crs=wqp_sites_dm.crs)

            for i, wqp_site in wqp_sites.iterrows():
                coord = [wqp_site.geometry.y,wqp_site.geometry.x]
                label = 'WQP Station: '+wqp_site.identifier
                html = label
                html += '<br>{0:s}'.format(wqp_site['name'])
                html += '<br><a href=\"{0:s}\" target=\"_blank\">{1:s}</a>'.format(wqp_site.uri,wqp_site.uri)
                html += '<br>Lat: {0:.4f}, Lon: {1:.4f}'.format(wqp_site.geometry.y,wqp_site.geometry.x)
                html += '<br>Comid: {0:s}'.format(wqp_site.comid)
                iframe = folium.IFrame(html,width=width,height=height)
                popup = folium.Popup(iframe,max_width=max_width)
                fg_wqp.add_child(folium.CircleMarker(location=coord,radius=radius,color=color,popup=popup,tooltip=label));

            fg_wqp.add_to(river_map);

            # Add HUC12 Pour Points, *differential* drainage basins, HUC4-10 boundaries associated with each

            fg_huc12pp = folium.FeatureGroup(name="HUC12 Pour Points",overlay=True,show=False)
            fg_basins = folium.FeatureGroup(name="Drainage Basins",overlay=True,show=False)
            fg_wbd4 = folium.FeatureGroup(name="HUC4 Boundaries",overlay=True,show=False)
            fg_wbd6 = folium.FeatureGroup(name="HUC6 Boundaries",overlay=True,show=False)
            fg_wbd8 = folium.FeatureGroup(name="HUC8 Boundaries",overlay=True,show=False)
            fg_wbd10 = folium.FeatureGroup(name="HUC10 Boundaries",overlay=True,show=False)
            fg_wbd12 = folium.FeatureGroup(name="HUC12 Boundaries",overlay=True,show=False)

            huc4_list = []
            huc6_list = []
            huc8_list = []
            huc10_list = []
            huc12_list = []

            color = 'darkblue'
            radius = 3
                    
            try:
                huc12pp_sites_dm = gpd.read_file(NWIS_SITE_NAV+"/DM/huc12pp?distance="+str(DM_DIST),driver='GeoJSON')
            except Exception as ex:
                print("An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args))
                huc12pp_sites_dm = gpd.GeoDataFrame()
                
            try:
                huc12pp_sites_um = gpd.read_file(NWIS_SITE_NAV+"/UM/huc12pp?distance="+str(UM_DIST),driver='GeoJSON')
            except Exception as ex:
                print("An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args))
                huc12pp_sites_um = gpd.GeoDataFrame()
                
            huc12pp_sites = gpd.GeoDataFrame(pd.concat([huc12pp_sites_dm,huc12pp_sites_um], ignore_index=True), crs=huc12pp_sites_dm.crs)

            n_segs = len(huc12pp_sites)-1

            # Sort sites by decreasing area of drainage basin
            def get_area(x):
                x_basin = gpd.read_file(USGS_NLDI_WS+"/comid/"+x+"/basin")
                return int(round(x_basin.iloc[0].geometry.area,3)*1000)  

            huc12pp_sites['area']=huc12pp_sites.apply(lambda x: get_area(x.comid), axis=1)
            huc12pp_sites.set_index(['area'],inplace=True,drop=True)
            huc12pp_sites.sort_index(inplace=True,ascending=False)

            i = 0

            for area, huc12pp_site in huc12pp_sites.iterrows():
                
                # Add to HUC12 PP to Site table in database

                # if (DB_NOT_FOUND):
                #     huc12pp = Site(type='HUC12PP',name=huc12pp_site.identifier,desc=huc12pp_site['name'],url=huc12pp_site.uri,comid=huc12pp_site.comid,geom='POINT({0:.4f} {1:.4f})'.format(huc12pp_site.geometry.x,huc12pp_site.geometry.y))
                #     spatialite_session.add(huc12pp)
                    
                # Get HUC12 PP drainage basin
                basin_url = USGS_NLDI_WS+"/comid/{0:s}/basin".format(huc12pp_site.comid)
                
                try:
                    basin = gpd.read_file(basin_url,driver='GeoJSON')
                except Exception as ex:
                    print("An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args))
                    i = i + 1
                    continue

                basin_area = GeomHelper.geom_area(basin)
                basin_diff_area = basin_area
                
                # Get HUC12 watershed boudary (WBD)
                wbd12_url = TNM_WS+"/wbd/MapServer/6/query?where=HUC12%3D%27{0:s}%27&outFields=NAME%2CHUC12%2CAREASQKM&f=geojson".format(huc12pp_site.identifier)
                
                try:
                    wbd12 = gpd.read_file(wbd12_url,driver='GeoJSON')
                except Exception as ex:
                    print("An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args))
                    i = i + 1
                    continue

                if i < n_segs:
                    # Add HUC12 boundary a feature layer
                    style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.1}
                    highlight_function = lambda x: {'color':'yellow', 'weight':2}
                    tooltip = "HUC12: {0:s} ({1:s}), Area: {2:.2f}".format(wbd12.iloc[0]['huc12'],wbd12.iloc[0]['name'],GeomHelper.geom_area(wbd12)[0])

                    wbd12_feature = folium.GeoJson(wbd12.iloc[0].geometry,style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                    fg_wbd12.add_child(wbd12_feature);        
                    huc12_list.append(huc12pp_site.identifier)


                if i > 0:
                    # Generate and show difference between sussessive drainage basins -- this is for the previous (downstream) basin, associated with previous HUC12 PP
                    basin_diff = gpd.overlay(basin_prev,basin,how='difference')  
                    basin_diff_area = GeomHelper.geom_area(basin_diff)
                    style_function = lambda x: {'color': 'red', 'weight': 1, 'fillColor': 'blue', 'fillOpacity': 0.1}
                    highlight_function = lambda x: {'color':'yellow', 'weight':3}
                    tooltip = "Differential Drainage Basin for HUC12 Pour Point: {0:s} ({1:s}), Area: {2:.2f}".format(wbd12.iloc[0]['huc12'],wbd12.iloc[0]['name'],basin_diff_area[0])
                    basin_diff_feature = folium.GeoJson(basin_diff.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                    fg_basins.add_child(basin_diff_feature);
                    
                    if i == n_segs:
                        # Show large basin of first (highest upstream) pour point
                        style_function = lambda x: {'color': 'gray', 'weight': 1, 'fillColor': 'gray', 'fillOpacity': 0.1}
                        highlight_function = lambda x: {'color':'yellow', 'weight':1}
                        tooltip = "Total Drainage Basin for HUC12 Pour Point: {0:s} ({1:s}), Area: {2:.2f}".format(wbd12.iloc[0]['huc12'],wbd12.iloc[0]['name'],basin_area[0])
                        basin_feature = folium.GeoJson(basin.iloc[0].geometry,style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                        fg_basins.add_child(basin_feature);
                        
                    # Get HUC10 containing HUC12 and add that to another feature layer 
                    huc10_identifier = huc12pp_prev[:-2]

                    wbd10_url = TNM_WS+"/wbd/MapServer/5/query?where=HUC10%3D%27{0:s}%27&outFields=NAME%2CHUC10%2CAREASQKM&f=geojson".format(huc10_identifier)
                    try:
                        wbd10 = gpd.read_file(wbd10_url)
                    except:
                        pass
                    else:
                        basin_huc10_overlap = gpd.overlay(wbd10,basin_diff,how='intersection')  

                        style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                        highlight_function = lambda x: {'color':'yellow', 'weight':2}
                        tooltip = "HUC10 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd10.iloc[0]['huc10'],wbd10.iloc[0]['name'],GeomHelper.geom_area(basin_huc10_overlap)[0])
                        wbd10_feature = folium.GeoJson(basin_huc10_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                        fg_wbd10.add_child(wbd10_feature);                 
                        if (huc10_identifier not in huc10_list):
                            tooltip = "HUC10: {0:s} ({1:s}), Area: {2:.2f}".format(wbd10.iloc[0]['huc10'],wbd10.iloc[0]['name'],wbd10.iloc[0].areasqkm)
                            wbd10_feature = folium.GeoJson(wbd10.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                            fg_wbd10.add_child(wbd10_feature);                 
                            huc10_list.append(huc10_identifier)

                    # Get HUC8 containing HUC12 and add that to another feature layer 
                    huc8_identifier = huc12pp_prev[:-4]

                    wbd8_url = TNM_WS+"/wbd/MapServer/4/query?where=HUC8%3D%27{0:s}%27&outFields=NAME%2CHUC8%2CAREASQKM&f=geojson".format(huc8_identifier)
                    try:
                        wbd8 = gpd.read_file(wbd8_url)
                    except:
                        pass
                    else:
                        basin_huc8_overlap = gpd.overlay(wbd8,basin_diff,how='intersection')  

                        style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                        highlight_function = lambda x: {'color':'yellow', 'weight':2}
                        tooltip = "HUC8 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd8.iloc[0]['huc8'],wbd8.iloc[0]['name'],GeomHelper.geom_area(basin_huc8_overlap)[0])
                        wbd8_feature = folium.GeoJson(basin_huc8_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                        fg_wbd8.add_child(wbd8_feature);                 
                        if (huc8_identifier not in huc8_list):
                            tooltip = "HUC8: {0:s} ({1:s}), Area: {2:.2f}".format(wbd8.iloc[0]['huc8'],wbd8.iloc[0]['name'],wbd8.iloc[0].areasqkm)
                            wbd8_feature = folium.GeoJson(wbd8.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                            fg_wbd8.add_child(wbd8_feature);                 
                            huc8_list.append(huc8_identifier)

                    # Get HUC6 containing HUC12 and add that to another feature layer 
                    huc6_identifier = huc12pp_prev[:-6]

                    wbd6_url = TNM_WS+"/wbd/MapServer/3/query?where=HUC6%3D%27{0:s}%27&outFields=NAME%2CHUC6%2CAREASQKM&f=geojson".format(huc6_identifier)
                    try:
                        wbd6 = gpd.read_file(wbd6_url)
                    except:
                        pass
                    else:
                        basin_huc6_overlap = gpd.overlay(wbd6,basin_diff,how='intersection')  

                        style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                        highlight_function = lambda x: {'color':'yellow', 'weight':2}
                        tooltip = "HUC6 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd6.iloc[0]['huc6'],wbd6.iloc[0]['name'],GeomHelper.geom_area(basin_huc6_overlap)[0])
                        wbd6_feature = folium.GeoJson(basin_huc6_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                        fg_wbd6.add_child(wbd6_feature);                 
                        if (huc6_identifier not in huc6_list):
                            tooltip = "HUC6: {0:s} ({1:s}), Area: {2:.2f}".format(wbd6.iloc[0]['huc6'],wbd6.iloc[0]['name'],wbd6.iloc[0].areasqkm)
                            wbd6_feature = folium.GeoJson(wbd6.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                            fg_wbd6.add_child(wbd6_feature);                 
                            huc6_list.append(huc6_identifier)

                    # Get HUC4 containing HUC12 and add that to another feature layer 
                    huc4_identifier = huc12pp_prev[:-8]

                    wbd4_url = TNM_WS+"/wbd/MapServer/2/query?where=HUC4%3D%27{0:s}%27&outFields=NAME%2CHUC4%2CAREASQKM&f=geojson".format(huc4_identifier)
                    try:
                        wbd4 = gpd.read_file(wbd4_url)
                    except:
                        pass
                    else:
                        basin_huc4_overlap = gpd.overlay(wbd4,basin_diff,how='intersection')  

                        style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                        highlight_function = lambda x: {'color':'yellow', 'weight':2}
                        tooltip = "HUC4 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd4.iloc[0]['huc4'],wbd4.iloc[0]['name'],GeomHelper.geom_area(basin_huc4_overlap)[0])
                        wbd4_feature = folium.GeoJson(basin_huc4_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                        fg_wbd4.add_child(wbd4_feature);                 
                        if (huc4_identifier not in huc4_list):
                            tooltip = "HUC4: {0:s} ({1:s}), Area: {2:.2f}".format(wbd4.iloc[0]['huc4'],wbd4.iloc[0]['name'],wbd4.iloc[0].areasqkm)
                            wbd4_feature = folium.GeoJson(wbd4.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                            fg_wbd4.add_child(wbd4_feature);                 
                            huc4_list.append(huc4_identifier)
                        
                basin_prev = basin
                huc12pp_prev = huc12pp_site.identifier

                # HUC12 Pour Point markers
                coord = [huc12pp_site.geometry.y,huc12pp_site.geometry.x]
                label = 'Pour Point for HUC12: '+wbd12.iloc[0]['name']
                html = label
                html += '<br>Indentifier: {0:s}'.format(huc12pp_site.identifier)
                html += '<br>Lat: {0:.2f}, Lon: {1:.2f}'.format(huc12pp_site.geometry.y,huc12pp_site.geometry.x)
                html += '<br>Comid: {0:s}'.format(huc12pp_site.comid)
                html += '<br>Area Total: {0:.2f}'.format(basin_area[0])
                html += '<br>Area Difference: {0:.2f}'.format(basin_diff_area[0])
                iframe = folium.IFrame(html,width=width,height=height)
                popup = folium.Popup(iframe,max_width=max_width)
                fg_huc12pp.add_child(folium.CircleMarker(location=coord,radius=radius,color=color,popup=popup,tooltip=label));
                
                i = i + 1

                basin_prev = basin
                huc12pp_prev = huc12pp_site.identifier

            # Do HUC2-10s for final upstream basin

            huc10_identifier = huc12pp_prev[:-2]

            wbd10_url = TNM_WS+"/wbd/MapServer/5/query?where=HUC10%3D%27{0:s}%27&outFields=NAME%2CHUC10%2CAREASQKM&f=geojson".format(huc10_identifier)
            try:
                wbd10 = gpd.read_file(wbd10_url)
            except:
                pass
            else:
                basin_huc10_overlap = gpd.overlay(wbd10,basin_diff,how='intersection')  

                style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                highlight_function = lambda x: {'color':'yellow', 'weight':2}
                tooltip = "HUC10 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd10.iloc[0]['huc10'],wbd10.iloc[0]['name'],GeomHelper.geom_area(basin_huc10_overlap)[0])
                wbd10_feature = folium.GeoJson(basin_huc10_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                fg_wbd10.add_child(wbd10_feature);                 
                if (huc10_identifier not in huc10_list):
                    tooltip = "HUC10: {0:s} ({1:s}), Area: {2:.2f}".format(wbd10.iloc[0]['huc10'],wbd10.iloc[0]['name'],wbd10.iloc[0].areasqkm)
                    wbd10_feature = folium.GeoJson(wbd10.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                    fg_wbd10.add_child(wbd10_feature);                 
                    huc10_list.append(huc10_identifier)

            huc8_identifier = huc12pp_prev[:-4]

            wbd8_url = TNM_WS+"/wbd/MapServer/4/query?where=HUC8%3D%27{0:s}%27&outFields=NAME%2CHUC8%2CAREASQKM&f=geojson".format(huc8_identifier)
            try:
                wbd8 = gpd.read_file(wbd8_url)
            except:
                pass
            else:
                basin_huc8_overlap = gpd.overlay(wbd8,basin_diff,how='intersection')  

                style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                highlight_function = lambda x: {'color':'yellow', 'weight':2}
                tooltip = "HUC8 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd8.iloc[0]['huc8'],wbd8.iloc[0]['name'],GeomHelper.geom_area(basin_huc8_overlap)[0])
                wbd8_feature = folium.GeoJson(basin_huc8_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                fg_wbd8.add_child(wbd8_feature);                 
                if (huc8_identifier not in huc8_list):
                    tooltip = "HUC8: {0:s} ({1:s}), Area: {2:.2f}".format(wbd8.iloc[0]['huc8'],wbd8.iloc[0]['name'],wbd8.iloc[0].areasqkm)
                    wbd8_feature = folium.GeoJson(wbd8.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                    fg_wbd8.add_child(wbd8_feature);                 
                    huc8_list.append(huc8_identifier)

            huc6_identifier = huc12pp_prev[:-6]

            wbd6_url = TNM_WS+"/wbd/MapServer/3/query?where=HUC6%3D%27{0:s}%27&outFields=NAME%2CHUC6%2CAREASQKM&f=geojson".format(huc6_identifier)
            try:
                wbd6 = gpd.read_file(wbd6_url)
            except:
                pass
            else:
                basin_huc6_overlap = gpd.overlay(wbd6,basin_diff,how='intersection')  

                style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                highlight_function = lambda x: {'color':'yellow', 'weight':2}
                tooltip = "HUC6 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd6.iloc[0]['huc6'],wbd6.iloc[0]['name'],GeomHelper.geom_area(basin_huc6_overlap)[0])
                wbd6_feature = folium.GeoJson(basin_huc6_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                fg_wbd6.add_child(wbd6_feature);                 
                if (huc6_identifier not in huc6_list):
                    tooltip = "HUC6: {0:s} ({1:s}), Area: {2:.2f}".format(wbd6.iloc[0]['huc6'],wbd6.iloc[0]['name'],wbd6.iloc[0].areasqkm)
                    wbd6_feature = folium.GeoJson(wbd6.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                    fg_wbd6.add_child(wbd6_feature);                 
                    huc6_list.append(huc6_identifier)

            huc4_identifier = huc12pp_prev[:-8]

            wbd4_url = TNM_WS+"/wbd/MapServer/2/query?where=HUC4%3D%27{0:s}%27&outFields=NAME%2CHUC4%2CAREASQKM&f=geojson".format(huc4_identifier)
            try:
                wbd4 = gpd.read_file(wbd4_url)
            except:
                pass
            else:
                basin_huc4_overlap = gpd.overlay(wbd4,basin_diff,how='intersection')  

                style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                highlight_function = lambda x: {'color':'yellow', 'weight':2}
                tooltip = "HUC4 Overlap: {0:s} ({1:s}), Area: {2:.2f}".format(wbd4.iloc[0]['huc4'],wbd4.iloc[0]['name'],GeomHelper.geom_area(basin_huc4_overlap)[0])
                wbd4_feature = folium.GeoJson(basin_huc4_overlap.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                fg_wbd4.add_child(wbd4_feature);                 
                if (huc4_identifier not in huc4_list):
                    tooltip = "HUC4: {0:s} ({1:s}), Area: {2:.2f}".format(wbd4.iloc[0]['huc4'],wbd4.iloc[0]['name'],wbd4.iloc[0].areasqkm)
                    wbd4_feature = folium.GeoJson(wbd4.iloc[0].geometry.buffer(-0.001).buffer(0.001),style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                    fg_wbd4.add_child(wbd4_feature);                 
                    huc4_list.append(huc4_identifier)

            fg_huc12pp.add_to(river_map);
            fg_basins.add_to(river_map);
            fg_wbd4.add_to(river_map);
            fg_wbd6.add_to(river_map);
            fg_wbd8.add_to(river_map);
            fg_wbd10.add_to(river_map);
            fg_wbd12.add_to(river_map);


            # Add HUC12s that are contained in the drainage basins
            #  * TODO: Search by shape

            fg_huc12_plus = folium.FeatureGroup(name="Other HUC12s in HUC10",overlay=True,show=False)
                    
            i = 0
            n_segs = len(huc12pp_sites)

            for area, huc12pp_site in huc12pp_sites.iterrows():
                if i >= n_segs - 1:
                    break
                    
                basin_url = USGS_NLDI_WS+"/comid/{0:s}/basin".format(huc12pp_site.comid)    
                try:
                    basin = gpd.read_file(basin_url,driver='GeoJSON')
                except:
                    i = i + 1
                    continue

                # Get HUC12 watershed boundaries sharing the same HUC10
                huc12_plus_url = TNM_WS+"/wbd/MapServer/6/query?where=HUC12%20LIKE%20%27{0:s}%25%27&outFields=NAME%2CHUC12%2CSHAPE_Length&f=geojson".format(huc12pp_site.identifier[:-2])

                try:
                    huc12_plus = gpd.read_file(huc12_plus_url,driver='GeoJSON')
                except:
                    i = i + 1
                    continue
                    
                huc12_basin_overlap = gpd.overlay(huc12_plus,basin,how='intersection')
                
                if (not huc12_basin_overlap.empty):
                    for k, huc12_in_basin in huc12_basin_overlap.iterrows():
                        huc12_wbd_url = TNM_WS+"/wbd/MapServer/6/query?where=HUC12%3D%27{0:s}%27&outFields=NAME%2CHUC12%2CSHAPE_Length&f=geojson".format(huc12_in_basin.huc12)
                        huc12_wbd = gpd.read_file(huc12_wbd_url,driver='GeoJSON')
                        huc12_overlap = gpd.overlay(huc12_wbd,basin,how='intersection')
                        if ((not huc12_overlap.empty) and (huc12_overlap.iloc[0].geometry.area > 0.001) and (huc12_in_basin.huc12 not in huc12_list)):
                            huc12_list.append(huc12_in_basin.huc12)
                            # Add HUC12 WBD boundary
                            style_function = lambda x: {'color': 'darkgreen', 'weight': 1, 'fillColor': 'green', 'fillOpacity': 0.05}
                            highlight_function = lambda x: {'color':'yellow', 'weight':2}
                            tooltip = "HUC12: {0:s} ({1:s}), Area: {2:.2f}".format(huc12_wbd.iloc[0]['huc12'],huc12_wbd.iloc[0]['name'],GeomHelper.geom_area(huc12_wbd)[0])
                            huc12_plus_feature = folium.GeoJson(huc12_wbd.iloc[0].geometry,style_function=style_function,highlight_function=highlight_function,tooltip=tooltip)
                            fg_huc12_plus.add_child(huc12_plus_feature);        
                                    
                i = i + 1

            fg_huc12_plus.add_to(river_map);


            # Add HUC12s that are contained in nearby HUC10s (in same HUC8 as the HUC12 Pour Point) and in the associated drainage basin
            # * TODO: How to exclude more distant HUC10s?

            # Add tributaries upstream of HUC12 Pour Points

            fg_utpp = folium.FeatureGroup(name="Tribs upstream of PPs",overlay=True,show=False)

            for huc12 in huc12_list:
                wbd12_url = TNM_WS+"/wbd/MapServer/6/query?where=HUC12%3D%27{0:s}%27&f=geojson".format(huc12)
                
                try:
                    wbd12 = gpd.read_file(wbd12_url)
                except:
                    continue
                    
                distance = int(round(GeomHelper.geom_diagonal(wbd12),0)) # May need to exend for winding streams
                #distance = 35
                tribs = folium.GeoJson(USGS_NLDI_WS+"/huc12pp/{0:s}/navigate/UT?distance={1:d}".format(huc12,distance))
                fg_utpp.add_child(tribs);
                
            fg_utpp.add_to(river_map);

            # Add water quality (WQP) properties

            wqp_property_series = []

            for i, wqp_site in wqp_sites.iterrows():
                if (IGNORE_WQP_DATES):
                    wqp_properties = pd.read_csv("https://www.waterqualitydata.us/data/Result/search?siteid="+wqp_site.identifier+"&mimeType=csv")
                else:
                    wqp_properties = pd.read_csv("https://www.waterqualitydata.us/data/Result/search?siteid="+wqp_site.identifier+"&startDateLo="+BEGIN_DATE+"&startDateHi="+END_DATE+"&mimeType=csv")
                    
                for i, wqp_property in wqp_properties.iterrows():
                    try:
                        this_property = wqp_property['CharacteristicName']
                        this_value = float(wqp_property['ResultMeasureValue'])
                        # this_datetime = datetime.strptime(wqp_property['ActivityStartDate']+' '+wqp_property['ActivityStartTime/Time'],"%Y-%m-%d %H:%M:%S")
                        this_datetime = datetime.strptime(wqp_property['ActivityStartDate'],"%Y-%m-%d")                
                        wqp_property_series.append((wqp_site.name,wqp_site.geometry.y,wqp_site.geometry.x,this_datetime,this_property,this_value))
                    except Exception as ex:
                        #print("An exception of type {0} occurred. Arguments:\n{1!r}".format(type(ex).__name__, ex.args))
                        continue

            wqp_property_table = pd.DataFrame(wqp_property_series, columns=['Site','Lat','Lon','Datetime','Property','Value'])
            wqp_property_table = wqp_property_table[wqp_property_table['Value'].notna()]
            wqp_summary_table = wqp_property_table.groupby(['Site','Property']).mean().reset_index()
            wqp_summary_table.rename(columns={"Value":"Avg"}, inplace=True)
            wqp_summary_table = wqp_summary_table[wqp_summary_table['Avg'].notna()]
            wqp_property_counts = wqp_property_table.groupby('Property').count()
            #n_sites = wqp_sites.count()
            wqp_top_properties = wqp_property_counts[wqp_property_counts["Site"]>3].sort_values('Site',ascending=False).index 

            fg_wqp_properties = folium.FeatureGroup(name='WQP Properties',overlay=True,show=True)
            _ = fg_wqp_properties.add_to(river_map);

            max_properties = 15 # maximum number of properties to map
            n_props = 0
            for wqp_top_property in wqp_top_properties:
                if (n_props > max_properties):
                    break;
                avg_val = wqp_property_table.query("Property == '"+wqp_top_property+"'")['Value'].mean()
                min_val = wqp_property_table.query("Property == '"+wqp_top_property+"'")['Value'].min()
                max_val = wqp_property_table.query("Property == '"+wqp_top_property+"'")['Value'].max()
                std_val = wqp_property_table.query("Property == '"+wqp_top_property+"'")['Value'].std()

                try:
                    if (math.isnan(avg_val) or math.isnan(std_val) or math.isnan(min_val) or math.isnan(max_val)):
                        continue
                except:
                    continue

                n_props = n_props + 1
                width = 500
                height = 90
                max_width = 1000 
                sfg_wqp_property = folium.plugins.FeatureGroupSubGroup(fg_wqp_properties,name=wqp_top_property[:20],overlay=True,show=False);

                wqp_site_summary = wqp_summary_table.query("Property == '"+wqp_top_property+"'")
                
                for i, wqp_site in wqp_site_summary.iterrows():
                    try:
                        if (math.isnan(wqp_site.Avg)):
                            continue
                    except:
                        continue
                    site = str(wqp_site.Site)
                    coord = [wqp_site.Lat,wqp_site.Lon]
                    value = float(wqp_site.Avg)
                    #radius = 5
                    z_value = (value-avg_val)/std_val
                    radius = min(7+2*abs(z_value),15)
                    color = ColorHelper.val2color(z_value,-2.0,2.0)
                    fill_color = color
                    label = "{0:s}: {1:s} = {2:.2f}".format(site,wqp_top_property,value)
                    html = label
                    #html += '<br>min = {0:.2f}, max = {1:.2f}'.format(min_val,max_val)
                    #html += '<br>color = '+color
                    html += '<br>'+site
                    #html += '<br>'+row.Description
                    html += '<br>Lat: {0:.2f}'.format(wqp_site.Lat)+', Lon: {0:.2f}'.format(wqp_site.Lon)
                    iframe = folium.IFrame(html,width=width,height=height)
                    popup = folium.Popup(iframe,max_width=max_width)
                    _ = sfg_wqp_property.add_child(folium.CircleMarker(location=coord,radius=radius,color=color,opacity=0.7,fill=True,fill_color=fill_color,fill_opacity=0.7,popup=popup,tooltip=label));
                _ = sfg_wqp_property.add_to(river_map);

            # Add built-in basemaps
            folium.TileLayer('StamenTerrain').add_to(river_map);
            folium.TileLayer('OpenStreetMap').add_to(river_map);

            # Add other basemap options using Map Servers at  ArcGIS Online
            mapserver_dict = dict(
                NatGeo_World_Map=ARCGIS_WS+'/NatGeo_World_Map/MapServer',
                World_Street_Map=ARCGIS_WS+'/World_Street_Map/MapServer',
                World_Imagery=ARCGIS_WS+'/World_Imagery/MapServer',
                World_Topo_Map=ARCGIS_WS+'/World_Topo_Map/MapServer',
                World_Shaded_Relief=ARCGIS_WS+'/World_Shaded_Relief/MapServer',
                World_Terrain_Base=ARCGIS_WS+'/World_Terrain_Base/MapServer',
            #   World_Physical_Map=ARCGIS_WS+'/World_Physical_Map/MapServer',  # only shows if zoomed out
            )
            mapserver_query = '/MapServer/tile/{z}/{y}/{x}'

            for tile_name, tile_url in mapserver_dict.items():
                tile_url += mapserver_query
                _ = folium.TileLayer(tile_url,name=tile_name,attr=tile_name).add_to(river_map);

            # Add the Layer Control widget
            folium.LayerControl().add_to(river_map);

            # Save the map as HTML
            river_map.save(OUT_DIR+'/wqpmap.html')

            # Creat an HTML template to embed the above in an iFrame
            f = open(OUT_DIR+'/index.html','w')
            html_text = """
<!DOCTYPE html>
<html>
<head>
<title>WQP Map </title>
</head>
<body>
<p>Reach: NWIS Station: {0} + {1} Km upstream - {2} Km downstream</p>
<p>Begin Date: {3}, End Date: {4} [Ignore dates for WQP properties: {5}]</p>
<br/>
<iframe src='wqpmap.html' name='iframe_map' style='height:600px;width:900px;' title='WQP Map'></iframe>
</body>
</html>""".format(NWIS_SITE,UM_DIST,DM_DIST,BEGIN_DATE,END_DATE,IGNORE_WQP_DATES) 
# TODO: include iFrame for Bokeh-generated time-series plots
# <iframe src='' name='iframe_plot' style='height:300px;width:900px;' title='Timeseries Plots'></iframe>
            f.write(html_text)
            f.close()
        except:
            raise GeoEDFError('Error occurred when running WQPMap processor: ')
    
