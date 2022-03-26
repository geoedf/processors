#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import numpy as np

from geoedfframework.utils.GeoEDFError import GeoEDFError

""" Helper module for converting nuneric values to colors 
"""
def val2color(value,min_value,max_value):
    try:
        if (math.isnan(value)):
            return '#000000'
        clip_value = np.clip(value,min_value,max_value)
        hue = int((clip_value-min_value)/(max_value-min_value)*255)
        red = hue
        green = 255 - 2*abs(hue-128)
        blue = 255 - hue
    except:
        raise GeoEDFError('Could not convert value to a color')
    
    return '#{0:02X}{1:02X}{2:02X}'.format(red,green,blue)

