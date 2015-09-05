#!/usr/bin/env python

########################################################################################################
#
# TITLE: geospatial.py
# AUTHOR: Jean-Guy Nistad
# 
# Copyright (C) 2015  Jean-Guy Nistad
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
########################################################################################################

"""
Library of common geospatial functions
"""

def decdeg2dms(dd):
    """Convert from decimal degrees to degree minute seconds representation

    Keyword arguments:
    dd -- decimal degrees

    Returns:
    a tuple containing (degrees, minutes, seconds)
    """
    negative = dd < 0
    dd = abs(dd)
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    if negative:
        if degrees > 0:
            degrees = -degrees
        elif minutes > 0:
            minutes = -minutes
        else:
            seconds = -seconds
    return (int(degrees),int(minutes),int(seconds))
        


def decdeg2dms_hem(dd, coord):
    """Convert from decimal degrees to degree minute seconds representation with handling of the hemisphere

    Keyword arguments:
    dd -- decimal degrees
    coord -- coordinate type as string ('lat' | 'lon')

    Returns:
    a tuple containing (degrees, minutes, seconds, hemisphere)
    """
    negative = dd < 0
    degrees, minutes, seconds = decdeg2dms(dd)
    degrees_abs = abs(degrees)
    if coord == 'lat':
        if negative:
            hem = 'S'
        else:
            hem = 'N'
    elif coord == 'lon':
        if negative:
            hem = 'W'
        else:
            hem = 'E'
    else:
        print "Unrecognized option for argument coord in decdeg2dms_hem"

    return (degrees_abs, minutes, seconds, hem)
    
