#!/usr/bin/env python

########################################################################################################
#
# TITLE: anbasemap.py
# AUTHOR: Jean-Guy Nistad
# DESCRIPTION: Create the ArcticNet 15' x 30' basemap tiles based on a given MB-System datalist
# DATE: April 25th, 2015
# VERSION: 1
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

"""

import math as m
import argparse
from sys import exit, argv
import os.path
import subprocess
import numpy as np
import geospatial as geo


# def write_tile_metadata():
#     """
#     """
#     from netCDF4 import Dataset
    
#     westBound = -119
#     eastBound = -55
#     southBound = 46
#     northBound = 82
#     numWE_tiles = 128
#     numSN_tiles = 144

#     # Vectors of longitude and latitude tiles
#     lats = np.linspace(northBound, southBound, num=numSN_tiles, endpoint=False)
#     lons = np.linspace(westBound, eastBound, num=numWE_tiles, endpoint=False)

#     # Fill-in the tilenames
#     tilenamesArray = np.empty(shape=(numSN_tiles,numWE_tiles), dtype='a21')
#     for y in lats:
#         yd, ym, ys, yh = geo.decdeg2dms_hem(y, 'lat')
#         for x in lons:
#             xd, xm, xs, xh = geo.decdeg2dms_hem(x, 'lon')
#             tilenamesArray[y][x] = "%.2d_%.2d_%.2d_%c_%.2d_%.2d_%.2d_%c" % (yd, ym, ys, yh, xd, xm, xs, xh)
#             print "Creating basemap tile %s..." % tilenamesArray[y][x]
    
#     # Matrix of longitude and latitude tiles
#     # lonArray = np.repeat(lons[np.newaxis, :], numSN_tiles, 0)
#     # latArray = np.repeat(lats[:, np.newaxis], numWE_tiles, 1)

#     # Create the netCDF dataset
#     dataset = Dataset('tileMetaDataset.nc', 'w', format='NETCDF4_CLASSIC')

#     # Add dimensions
#     lat = dataset.createDimension('lat', numSN_tiles)
#     lon = dataset.createDimension('lon', numWE_tiles)

#     # Add variables
#     latitudes  = dataset.createVariable('latitude', np.float32, ('lat',))
#     longitudes = dataset.createVariable('longitude', np.float32, ('lon',))
#     tilenames = dataset.createVariable('tilename', np.dtype='a21', ('lat','lon',))
    
#     # Write data
#     latitudes[:]  = lats
#     longitudes[:] = lons
#     tilenames[:] = tilenamesArray



#     # Close the netCDF dataset
#     dataset.close()



    
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
    
    
    
def make_EHdr_grid(datalist, region, output_dir, tilename, cellsize):
    """Make an ESRI EHdr Lambert conformal conic projected grid

    Keyword arguments:
    datalist -- MB-System datalist
    region -- GMT region in the W/E/S/N format
    output_dir -- directory path in which to store the map
    tilename -- Name of the tile
    """
    # Grid
    print "Gridding with %s m cell size..." % (cellsize)
    subprocess.call(["mbgrid", "-I", datalist, "-A2", "-F5", "-N", "-R"+region, "-JAmundsenLambert", "-E"+str(cellsize)+"/0.0/meters!", "-O", output_dir+"/"+tilename+"_Ztopo_lcc", "-V"])

    # Get the projected limits
    proj_limit_file = proj_limits(region, output_dir+"/"+tilename)
    
    # Mask based on projected coordinates
    subprocess.call(["grdmask", proj_limit_file, "-G"+output_dir+"/"+tilename+"_Ztopo_lcc_mask.grd", "-R"+output_dir+"/"+tilename+"_Ztopo_lcc.grd", "-NNaN/1/1", "-V"])

    # Perform mask
    subprocess.call(["grdmath", output_dir+"/"+tilename+"_Ztopo_lcc.grd", output_dir+"/"+tilename+"_Ztopo_lcc_mask.grd", "OR", "=", output_dir+"/"+tilename+"_Ztopo_lcc_tiled.grd"])

    # Change the output format
    subprocess.call(["gdal_translate", "-a_srs", "+proj=lcc +lat_1=70 +lat_2=73 +lat_0=70 +lon_0=-105 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs", "-of", "EHdr", "-a_nodata", "0", output_dir+"/"+tilename+"_Ztopo_lcc_tiled.grd", output_dir+"/"+tilename+"_Ztopo_lcc_tiled.flt"])
    

    
def make_gif_map(datalist, region, output_dir, tilename, logo, cellsize):
    """Make a GIF file of the ArcticNet tile

    Keyword arguments:
    datalist -- MB-System datalist
    region -- GMT region in the W/E/S/N format
    output_dir -- directory path in which to store the map
    tilename -- Name of the tile
    logo -- Name of the logo to place in postscript map
    """

    # Check if the logo file exists
    if not os.path.isfile(output_dir+"/"+logo):
        print 'Could not find file %s. Please correct and try running the program again' % logo
        exit()
    else:
        print '%s found in directory.' % logo
    
    # Grid
    print "Gridding with %s m cell size..." % (cellsize)
    subprocess.call(["mbgrid", "-I", datalist, "-A2", "-F5", "-N", "-R"+region, "-E"+str(cellsize)+"/0.0/meters!", "-O", output_dir+"/"+tilename+"_Ztopo", "-V"])

    # Specify the position (lon, lat) of the directional rose (north arrow)
    roseLon = float(region.split('/')[1]) - 5/60.
    roseLat = float(region.split('/')[3]) - 2/60.
    rosePos = "%.5f/%.5f" % (roseLon, roseLat)

    #  Write the GMT script and execute it
    write_gmt_script(output_dir, tilename, tilename+'_Ztopo.grd', region, rosePos)
    subprocess.call(["chmod", "u+x", output_dir+"/"+tilename+".sh"])
    print "\n\n--------------\n\n"
    print "Instructions:"
    print "Execute <%s> to create the map in postscript and gif format." % (output_dir+"/"+tilename+".sh")
    print "\n\n--------------\n\n"
    #subprocess.call(["./"+tilename+".sh"])

    
    
def write_gmt_script(output_dir, filename, Ztopo, region, rosePos):
    """Write a GMT bash script for a basemap tile

    Keyword arguments:
    output_dir -- output directory to store the product
    filename -- name of file to write
    Ztopo -- name of the geographic bathymetric grid in NetCDF format
    region -- geographic extent
    rosePos -- position of the directional rose on the map
    """
    out = open(output_dir+"/"+filename+'.sh', 'w')
    out.write('''#!/bin/bash

PATH=$PATH:/usr/lib/gmt/bin
################################################################################################################################
## Title: {filename}.sh
## Author: Jean-Guy Nistad
## Projection: Lambert conic conformal
## Descripion: This GMT script creates an ArctiNet Basemap Tile
## Usage: ./{filename}.sh
## Required UNIX programs: GMT version 4.5.6 or higher, Imagemagick
## Required input arguments:
##      1) The name of the basemap tile to create
##      2) The netCDF grid of the geographic bathymetric grid to be displayed in the tile. The grid should have been generated
##         a-priori using MB-System's mbgrid command.
##      3) the logo to be displayed in the legend. The logo must have the name logos.sun and be present in the current directory
################################################################################################################################

# Set GMT variables
gmtset PAPER_MEDIA=Letter
gmtset DOTS_PR_INCH=300
gmtset ANNOT_FONT_PRIMARY=Helvetica-Bold
gmtset ANNOT_FONT_SIZE=0.5c
gmtset X_ORIGIN=0c
gmtset Y_ORIGIN=0c
gmtset ELLIPSOID=WGS-84
gmtset PAGE_ORIENTATION=portrait
gmtset FRAME_WIDTH=1.25p
gmtset BASEMAP_TYPE=plain

# Required input variables
tilename={filename}
data={Ztopo}
logos=logos.sun
out={filename}.ps

# Generated temporary variables
data_i=Ztopo_cut_i.nc

# Map variables
width=15c
proj=L-105/70/70/73/$width
region={region}
annot=0.5/0.25

# Make a color palette
grd2cpt $data -Cjet -V -Z > colorbar.cpt

# Create a hillshade
grdgradient $data -Ne0.5 -A270 -G$data_i

# Griddding
grdimage $data -J$proj -R$region -Xa3c -Ya7.5c -Ccolorbar.cpt -I$data_i -Q -V -K > $out

# Background
psbasemap -J$proj -R$region -B$annot -Xa3c -Ya7.5c -T{rosePos}/1.5c --HEADER_FONT_SIZE=0.5c -V -K -O >> $out

# Append the legend
pslegend -J$proj -R$region -Dx0.25c/0.25c/21.1c/4c/BL -F -V -O << EOF >> $out
G -1c
B colorbar.cpt 4c 0.5c -A -B20 --ANNOT_FONT_PRIMARY=1 --ANNOT_FONT_SIZE=10 -S
I logos.sun 4c RT
G -2.6c
L 8 1 L @;128/128/128;Title:@;;
L 8 1 L Amundsen Basemap Tile $tilename
G 0.1c
L 8 1 L @;128/128/128;Datatype:@;;
L 8 1 L Bathymetry gridded at 10m planimetric resolution
G 0.1c
L 8 1 L @;128/128/128;Projection:@;;
L 8 1 L Lambert Conic Conformal
G 0.1c
L 8 1 L @;128/128/128;Horizontal Datum:@;;
L 8 1 L WGS84(G1150)
G 0.1c
L 8 1 L @;128/128/128;Vertical Datum:@;;
L 8 1 L Mean Sea Level
G -1.5c
M - 74 10+u f -J$proj -R$region
EOF

# Clean up
rm colorbar.cpt
rm $data_i

convert -density 240 -flatten $out $tilename.gif
'''.format(filename=filename, Ztopo=Ztopo, region=region, rosePos=rosePos))
    out.close()

    

def main():
    K_EHDR_GRD = 0
    K_GIF_MAP = 1
    K_EHDR_AND_GIF = 2
    
    parser = argparse.ArgumentParser(description="Create the ArcticNet 15' x 30' basemap tiles based on a given MB-System datalist")
    parser.add_argument('datalist', type=str, help='MB-System datalist to process')
    parser.add_argument('-D', '--outputDir', help='output directory in which to store the products')
    parser.add_argument('-l', '--logo', default='logos.sun', help='logo to display in legend. Default: logos.sun')
    parser.add_argument('cellsize', type=float, help='cell size')
    parser.add_argument('action', type=int, choices=[0,1,2], help='action to be performed. 0=make EHdr grid; 1=make GIF map; 2=make both')
    args = parser.parse_args()
 
    lon_step = 0.5
    lat_step = 0.25
  
    # Check that mb-system is installed
    try:
        subprocess.check_call(['which', 'mbinfo'])
    except subprocess.CalledProcessError:
        print 'Could not call mbinfo! Please make sure MB-Sysem is properly installed.'
        exit()
    else:
        print 'Running mbinfo...'     
        
    # Get the true bounds of datalist
    bounds = subprocess.check_output("mbinfo -F-1 -G -I %s | grep -E 'Longitude|Latitude'"  % (args.datalist), shell=True)   
    xmin_true = bounds.splitlines()[0].split()[2]
    xmax_true = bounds.splitlines()[0].split()[5]
    ymin_true = bounds.splitlines()[1].split()[2]
    ymax_true = bounds.splitlines()[1].split()[5]

    # Compute the bounds for the ArcticNet basemap tiles
    xmin_tile = round_bounds(xmin_true, lon_step, 'down')
    xmax_tile = round_bounds(xmax_true, lon_step, 'up')
    ymin_tile = round_bounds(ymin_true, lat_step, 'down')
    ymax_tile = round_bounds(ymax_true, lat_step, 'up')

    # Create the loop lists
    xsteps = (xmax_tile - xmin_tile) / lon_step
    ysteps = (ymax_tile - ymin_tile) / lat_step
    lon = np.linspace(xmin_tile, xmax_tile, num=xsteps, endpoint=False)
    lat = np.linspace(ymax_tile, ymin_tile, num=ysteps, endpoint=False)
  
    # Main loop over tiles from top-left corner
    cnt = 0
    for y in lat:
        yd, ym, ys, yh = geo.decdeg2dms_hem(y, 'lat')
        for x in lon:
            cnt = cnt + 1
            xd, xm, xs, xh = geo.decdeg2dms_hem(x, 'lon')
            tilename = "%.2d_%.2d_%.2d_%c_%.2d_%.2d_%.2d_%c" % (yd, ym, ys, yh, xd, xm, xs, xh)
            print "Creating basemap tile %d for tilename %s..." % (cnt, tilename)

            # Region of the tile
            region = "%.1f/%.1f/%.2f/%.2f" % (x, x+lon_step, y-lat_step, y)

            # See if data is contained within the current tile
            data_records = subprocess.check_output("mbinfo -F-1 -G -I %s -R %s | grep 'Number of Records:'" % (args.datalist, region), shell=True)
            numRec = int(data_records.split(':')[1].strip())

            # Execute main action if there is data to work on
            if (numRec > 0):
                if ((args.action == K_EHDR_GRD) or (args.action == K_EHDR_AND_GIF)):
                    make_EHdr_grid(args.datalist, region, args.outputDir, tilename, args.cellsize)
                if ((args.action == K_GIF_MAP) or (args.action == K_EHDR_AND_GIF)):
                    make_gif_map(args.datalist, region, args.outputDir, tilename, args.logo, args.cellsize)
            else:
                print "No data to grid for tilename %s!" % (tilename)

            
            
if __name__ == '__main__':
    print 'Running as script...'
    main()
    print 'Done with script.'
