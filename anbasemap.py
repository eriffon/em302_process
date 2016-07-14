#!/usr/bin/env python

########################################################################################################
#
# TITLE: anbasemap.py
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
Create the ArcticNet 15' x 30' basemap tiles based on a given MB-System datalist
"""

import math as m
import argparse
from sys import exit, argv
from os import path
import subprocess
import numpy as np
import geospatial as geo
import basetile_bathy as btbathy
import basetile_amp as btamp
import basetile_ss as btss

    
def round_bounds(x, base=0.5, direction='up'):
    """Round a floating point value up or down according to base

    Keyword arguments:
    x -- number to round
    base -- base to which to round. Default 0.5.
    direction -- round up or down depending on value. Default up.
    """
    if direction == 'up':
        return base * m.ceil(float(x) / base)
    elif direction == 'down':
        return base * m.floor(float(x) / base)
    


def proj_limits(region, path_tilename):
    """Generate a file containing the projection coordinate limits of the tile

    Keyword arguments:
    region -- GMT region in the W/E/S/N format
    path_tilename -- Path and Name of the tile

    Returns:
    filename -- a variable to the file containing the projection coordinate limites of the tile
    """
    import pyproj

    # Open a file to store results
    filename = path_tilename+'_lcc_coord.txt'
    out = open(filename, 'w')
    
    # Source and destination coordinate systems
    p1 = pyproj.Proj('+proj=latlong +datum=WGS84')
    p2 = pyproj.Proj('+proj=lcc +lat_1=70 +lat_2=73 +lat_0=70 +lon_0=-105 +x_0=2000000 +y_0=2000000 +datum=WGS84')

    # Parse the geographic coordinates
    xmin = float(region.split('/')[0])
    xmax = float(region.split('/')[1])
    ymin = float(region.split('/')[2])
    ymax = float(region.split('/')[3])

    # Transform
    ul = pyproj.transform(p1, p2, xmin, ymax)
    ur = pyproj.transform(p1, p2, xmax, ymax)
    lr = pyproj.transform(p1, p2, xmax, ymin)
    ll = pyproj.transform(p1, p2, xmin, ymin)

    # Print to file
    out.write('''{ulx} {uly}
{urx} {ury}
{lrx} {lry}
{llx} {lly}
{ulx} {uly}'''.format(ulx=ul[0], uly=ul[1], urx=ur[0], ury=ur[1], lrx=lr[0], lry=lr[1], llx=ll[0], lly=ll[1]))

    # Close the file and return
    out.close()

    return filename
    
    
    
def main():
    LON_STEP = 0.5
    LAT_STEP = 0.25
    
    parser = argparse.ArgumentParser(description= \
                                     "Create the ArcticNet 15' x 30' basemap tiles based on a given MB-System datalist, region and spatial resolution")
    parser.add_argument('datalist', type=str, help='MB-System datalist')
    parser.add_argument('datatype', type=int, default='2', help='MB-System datatype (bathymetry = 1; amplitude = 2; sidescan = 3')
    parser.add_argument('gridkind', type=int, default='1', help='MB-System gridkind (netCDF = 1; ESRI Grid = 2')
    parser.add_argument('mapkind',  type=int, default='1', help='MB-System mapkind (Postscript = 1; gif = 2')
    parser.add_argument('region',   type=str, help='region in west/east/south/north format')
    parser.add_argument('cellsize', type=float, help='cellsize')
    parser.add_argument('-D', '--outdir', help='output directory in which to store the products')
    parser.add_argument('-l', '--logo', default='logos.sun', help='logo to display in legend. Default: logos.sun')
    args = parser.parse_args()
   
    # Check that mb-system is installed
    try:
        subprocess.check_call(['which', 'mbinfo'])
    except subprocess.CalledProcessError:
        print 'Could not call mbinfo! Please make sure MB-Sysem is properly installed.'
        exit()

    # Split the region boundaries    
    (xmin_true, xmax_true, ymin_true, ymax_true) = args.region.split('/')
    
    # Compute the bounds for the ArcticNet basemap tiles
    xmin_tile = round_bounds(xmin_true, LON_STEP, 'down')
    xmax_tile = round_bounds(xmax_true, LON_STEP, 'up')
    ymin_tile = round_bounds(ymin_true, LAT_STEP, 'down')
    ymax_tile = round_bounds(ymax_true, LAT_STEP, 'up')
    
    # Create the loop lists
    xsteps = (xmax_tile - xmin_tile) / LON_STEP
    ysteps = (ymax_tile - ymin_tile) / LAT_STEP
    lon = np.linspace(xmin_tile, xmax_tile, num=xsteps, endpoint=False)
    lat = np.linspace(ymax_tile, ymin_tile, num=ysteps, endpoint=False)

    # Create a new sub-datalist with filename composed with region extent
    xmind, xminm, xmins, xminh = geo.decdeg2dms_hem(float(xmin_true), 'lon')
    xmaxd, xmaxm, xmaxs, xmaxh = geo.decdeg2dms_hem(float(xmax_true), 'lon')
    ymind, yminm, ymins, yminh = geo.decdeg2dms_hem(float(ymin_true), 'lat')
    ymaxd, ymaxm, ymaxs, ymaxh = geo.decdeg2dms_hem(float(ymax_true), 'lat')

    subdatalist = 'mbdatalist' +'_' + \
                  str(xmind) + 'd' + str(xminm) + 'm' + xminh + '_to_' + \
                  str(xmaxd) + 'd' + str(xmaxm) + 'm' + xmaxh + '_and_' + \
                  str(ymind) + 'd' + str(yminm) + 'm' + yminh + '_to_' + \
                  str(ymaxd) + 'd' + str(ymaxm) + 'm' + ymaxh + '.mb-1'

    # Check if a datalist for the specified region already exists. If it does, let the user decide whether to use this datalist ('e') or recreate a new one ('c')
    choice = 'c'     # Force the creation of the datalist. Only changed if the file exists and the use wishes to use the existing datalist.
    if path.isfile(subdatalist):
        print "\nThe datalist %s already exists! Would you like to use the existing datalist or create a new one?\n" % (subdatalist)
        choices = set(['e', 'c'])
        choice = raw_input('Enter your choice: use existing (\'e\') or create a new datalist (\'c\')?: ')
        while not choices.intersection(choice):
            choice = raw_input('Try again: use existing (\'e\') or create a new datalist (\'c\')?: ')

    if (choice == 'c'):
        try:
            subprocess.check_call(['which', 'mbdatalist'])
        except selfubprocess.CalledProcessError:
            print "\nCould not call mbdatalist! Please make sure MB-Sysem is properly installed\n."
            exit(-1)
        else:
            print "Running mbdatalist to generate datalist %s.\n"  % (subdatalist)
            print "Please be patient. This may take some time...\n"
            subprocess.check_output("mbdatalist -F-1 -I %s -R%s > %s" % (args.datalist, args.region, subdatalist), shell=True)
    elif (choice == 'e'):
        print "using existing datalist %s\n" % (subdatalist)   

    # Access the sub-datalist and check it's size
    f_datalist = open(subdatalist)
    f_datalist.seek(0,2)
    subdatalist_size = f_datalist.tell()

    if (subdatalist_size > 0):   
        # Main loop over tiles from top-left corner
        cnt = 0
        for y in lat:
            yd, ym, ys, yh = geo.decdeg2dms_hem(y, 'lat')
            for x in lon:
                cnt = cnt + 1
                xd, xm, xs, xh = geo.decdeg2dms_hem(x, 'lon')
                tilename = "%.2d_%.2d_%c_%.2d_%.2d_%c" % (yd, ym, yh, xd, xm, xh)
                print "Creating basemap tile %d for tilename %s..." % (cnt, tilename)

                # Region of the tile
                region = "%.1f/%.1f/%.2f/%.2f" % (x, x+LON_STEP, y-LAT_STEP, y)
               
                if (args.datatype == 1 or args.datatype == 2):
                    # Instantiate a bathy grid
                    tile = btbathy.BasetileBathy(tilename, region, args.cellsize)

                    # Make a bathy NetCDF grid
                    tile.make_bathy_grid(subdatalist, args.outdir)
                    # Make optional grid
                    if (args.gridkind == 2):
                        tile.make_esri_grid(args.outdir)

                    # Make the Postscript map
                    tile.make_bathy_ps_plot(args.outdir, args.logo)
                    # Make option gif image
                    if (args.mapkind == 2):
                        tile.make_gif_plot(args.outdir, args.logo)
                            
                elif (args.datatype == 3):
                    # Instantiate an amplitude grid
                    tile = btamp.BasetileAmp(tilename, region, args.cellsize)

                    # Make an amplitude NetCDF grid
                    tile.make_amp_grid(subdatalist, args.outdir)
                    # Make optional grid
                    if (args.gridkind == 2):
                        tile.make_esri_grid(args.outdir)

                    # Make an amplitude Postscript map
                    tile.make_amp_ps_plot(args.outdir, args.logo)
                    # Make option gif image
                    if (args.mapkind == 2):
                        tile.make_gif_plot(args.outdir, args.logo)
                            
                elif (args.datatype == 4):
                    # Instantiate an amplitude grid
                    tile = btss.BasetileSs(tilename, region, args.cellsize)

                    # Make an sidescan NetCDF grid
                    tile.make_ss_grid(subdatalist, args.outdir)
                    # Make optional grid
                    if (args.gridkind == 2):
                        tile.make_esri_grid(args.outdir)

                    # Make a sidescan Postscript map
                    tile.make_ss_ps_plot(args.outdir, args.logo)
                    # Make option gif image
                    if (args.mapkind == 2):
                        tile.make_gif_plot(args.outdir, args.logo)
                    
    else:
#        print "No data to grid for tilename %s!\n" % (tilename)
         print "No data to grid!\n"

    # Close the datalist file
    f_datalist.close()

            
if __name__ == '__main__':
    # print 'Running as script...'
    main()
    # print 'Done with script.'
