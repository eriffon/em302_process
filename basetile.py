#!/usr/bin/env python

########################################################################################################
#
# TITLE: basetile.py
# AUTHOR: Jean-Guy Nistad
# DESCRIPTION: Class for basemap tiles
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

from os import path, remove
from sys import exit
import subprocess

class Basetile(object):
    """ArcticNet basemap tile and associated functionnalities"""


    # Class attributes
    __suffix = {'grid': '_Ztopo_lcc', \
                'mask': '_mask', \
                'tile': '_tile', \
                'polygon': '_lcc_coord.txt', \
                'psmap': '_ZtopoSun', \
                'psmap_lcc': '_ZtopoSun_lcc'}
    
    __extension = {'grd': '.grd', \
                   'flt': '.flt', \
                   'cmd': '.cmd'}
    

    def __get_region(self, region, src_proj, dst_proj):
        """Extract all components of the region in geodesic and projected coordinates

        Keyword argument:
        region -- geographic extent of the tile
        """
        import pyproj

        # Dictionnary to store tile geo metadata
        geoinfo = dict()
        
        # Source and destination coordinate systems
        p1 = pyproj.Proj(src_proj)
        p2 = pyproj.Proj(dst_proj)

        # Parse the geographic coordinates
        geoinfo['geo'] = region
        geoinfo['xmin'] = float(region.split('/')[0])
        geoinfo['xmax'] = float(region.split('/')[1])
        geoinfo['ymin'] = float(region.split('/')[2])
        geoinfo['ymax'] = float(region.split('/')[3])           
            
        # Get the projected coordinates
        geoinfo['ul'] = pyproj.transform(p1, p2, geoinfo['xmin'], geoinfo['ymax'])
        geoinfo['ur'] = pyproj.transform(p1, p2, geoinfo['xmax'], geoinfo['ymax'])
        geoinfo['lr'] = pyproj.transform(p1, p2, geoinfo['xmax'], geoinfo['ymin'])
        geoinfo['ll'] = pyproj.transform(p1, p2, geoinfo['xmin'], geoinfo['ymin'])

        return geoinfo
    
    
    def __init__(self, name, region, cellsize):
        """Create and initialize a new basetile object

        Keyword arguments:
        name -- name of the basemap tile
        region -- geographic extent of the tile
        cellsize -- the spatial resolution of the tile
        """
        PROJ4_LCC = "+proj=lcc +lat_1=70 +lat_2=73 +lat_0=70 +lon_0=-105 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs" 
        PROJ4_GEO = "+proj=latlong +datum=WGS84"
        GMT_SCALE = "-105/70/70/73/"
        GMT_PROJ = "l"
        
        # Instance attributes
        self.name = name
        self.region = self.__get_region(region, PROJ4_GEO, PROJ4_LCC)
        self.cellsize = cellsize
        self.proj4_proj_lcc = PROJ4_LCC
        self.proj4_proj_geo = PROJ4_GEO
        self.gmt_proj = GMT_PROJ
        self.gmt_scale = GMT_SCALE
        self.nc_grid_no_ext = self.name+self.__suffix['grid']
        self.nc_grid = self.nc_grid_no_ext+self.__extension['grd']
        self.nc_grid_mask = self.nc_grid_no_ext+self.__suffix['mask']+self.__extension['grd']
        self.nc_grid_tile = self.nc_grid_no_ext+self.__suffix['tile']+self.__extension['grd']
        self.nc_cmd_script = self.nc_grid+self.__extension['cmd']
        self.esri_grid = self.nc_grid_no_ext+self.__suffix['tile']+self.__extension['flt']
        self.ps_map_no_ext = self.name+self.__suffix['psmap']
        self.ps_map_shell = self.ps_map_no_ext+self.__extension['cmd']
        self.ps_map_lcc_no_ext = self.name+self.__suffix['psmap_lcc']
        self.ps_map_lcc_shell = self.ps_map_lcc_no_ext+self.__extension['cmd']
        
        
    def __str__(self):
        """print the class attributes"""

        return "ArcticNet basemap tile %s with region %s and spatial resolution %s meters" \
            % (self.name, self.region, self.cellsize)


        
    def make_poly_ascii(self, outdir):
        """Generate a ascii file containing coordinates defining the tile's region

        Keyword arguments:
        outdir -- directory path in which to store the ascii file

        Returns:
        filename -- complete path to the ascii file
        """
        import pyproj
       
        # Open a file to store results
        filename = outdir+self.name+self.__suffix['polygon']
        out = open(filename, 'w')

        # Print to file
        out.write('''{ulx} {uly}
{urx} {ury}
{lrx} {lry}
{llx} {lly}
{ulx} {uly}'''.format(ulx=self.region['ul'][0], \
                      uly=self.region['ul'][1], \
                      urx=self.region['ur'][0], \
                      ury=self.region['ur'][1], \
                      lrx=self.region['lr'][0], \
                      lry=self.region['lr'][1], \
                      llx=self.region['ll'][0], \
                      lly=self.region['ll'][1]))

        # Close the file and return
        out.close()
        return filename


    
    def make_netcdf_grid(self, datalist, outdir):
        """Make a NetCDF grid from the specified datalist

        Keyword arguments:
        datalist -- MB-System datalist
        outdir -- directory path in which to store the grid
        """
        if not(path.isfile(datalist)):
            print "\nError: no such file %s found.\n" % (datalist)
            exit(-1)
        
        # Grid
        try:
            subprocess.check_call(['which', 'mbgrid'])
        except subprocess.CalledProcessError:
            print "\nCould not call mbgrid! Please make sure MB-Sysem is properly installed\n."
            exit(-1)
        else:
            print "Gridding with %s m cell size..." % (self.cellsize)
            subprocess.call(["mbgrid", "-I", datalist, \
                             "-A2", "-F5", "-N", \
                             "-R"+self.region['geo'], \
                             "-JAmundsen", \
                             "-E"+str(self.cellsize)+"/0.0/meters!", \
                             "-O", outdir+self.nc_grid_no_ext, "-V"])

        # Make polygon in projected coordinates
        polyfile = self.make_poly_ascii(outdir)
        
        # Mask based on projected polygon
        try:
            subprocess.check_call(['which', 'grdmask'])
        except subprocess.CalledProcessError:
            print "\nCould not call grdmask! Please make sure GMT is properly installed\n."
            exit(-1)
        else:            
            subprocess.call(["grdmask", polyfile, "-G"+outdir+self.nc_grid_mask, "-R"+outdir+self.nc_grid, "-NNaN/1/1", "-V"])

        # Perform mask
        try:
            subprocess.check_call(['which', 'grdmath'])
        except subprocess.CalledProcessError:
            print "\nCould not call grdmath! Please make sure GMT is properly installed\n."
            exit(-1)
        else:        
            subprocess.call(["grdmath", outdir+self.nc_grid, outdir+self.nc_grid_mask, "OR", "=", outdir+self.nc_grid_tile])

        # Remove unnecessary files
        if path.isfile(polyfile):
            # polygon file
            remove(polyfile)

        if path.isfile(outdir+self.nc_grid):
            # NetCDF grid
            remove(outdir+self.nc_grid)
            
        if path.isfile(outdir+self.nc_grid_mask):
            # NetCDF grid mask
            remove(outdir+self.nc_grid_mask)
          
        if path.isfile(outdir+self.nc_cmd_script):
            # csh grid script
            remove(outdir+self.nc_cmd_script)

            

    def make_esri_grid(self, outdir):
        """Make a NetCDF grid from the pre-generated NetCDF grid

        Keyword arguments:
        outdir -- directory path in which to store the grid
        """
        if path.isfile(outdir+self.nc_grid_tile):
            # Convert NetCDF grid to ESRI Grid
            try:
                subprocess.check_call(['which', 'gdal_translate'])
            except subprocess.CalledProcessError:
                print "\nCould not call gdal_translate! Please make sure GDAL is properly installed\n."
                exit(-1)
            else:                
                subprocess.call(["gdal_translate", "-a_srs", self.proj4_proj_lcc, "-of", "EHdr", "-a_nodata", "-99999", outdir+self.nc_grid_tile, outdir+self.esri_grid])
        else:
            print "\nError: NetCDF file %s not found!\n" % (self.nc_grid_tile)


    def lam2geo_carto(self, org_cmd, new_cmd):
        """Modify a c-shell script generated by MB-System's mb_grdplot command to replace the default Lambert basemap to a geographic basemap

        Keyword arguments:
        org_cmd -- name of the original c-shell script
        new_cmd -- name of the modified c-shell script
        """
        org_cmd_f = open(org_cmd, 'r')
        new_cmd_f = open(new_cmd, 'w')

        sections = {}

        org_lines = org_cmd_f.readlines()
        new_lines = org_lines
        
        for index, line in enumerate(org_lines):
            if 'shell variables' in line:
                if not sections.has_key('shell variable'):
                    sections['shell variable'] = {}
                    for i in range(6):
                        (key,val) = org_lines[index+i+1].split('=',1)
                        key = key.strip()
                        val = val.strip()
                        sections['shell variable'][key] = val

                # Modify the output Postcript filename
                sections['shell variable']['set PS_FILE'] = sections['shell variable']['set PS_FILE']. \
                                                            replace(self.__suffix['psmap'], self.__suffix['psmap_lcc'])
                new_lines[index + 1] = "set PS_FILE         = %s\n" % (sections['shell variable']['set PS_FILE'])

                # Modify the output CPT filename
                sections['shell variable']['set CPT_FILE'] = sections['shell variable']['set CPT_FILE']. \
                                                            replace(self.__suffix['psmap'], self.__suffix['psmap_lcc'])
                new_lines[index + 2] = "set CPT_FILE        = %s\n" % (sections['shell variable']['set CPT_FILE'])

                # Add a Lambert projection for psbasemap
                sections['shell variable']['set MAP_PROJECTION2'] = 'l'
                new_lines.insert(index + 4, "set MAP_PROJECTION2 = %s\n" % (sections['shell variable']['set MAP_PROJECTION2']))

                # Compute the plot width
                xmax = float(self.region['lr'][0])
                xmin = float(self.region['ul'][0])
                map_scale = float(sections['shell variable']['set MAP_SCALE'])
                plot_width = map_scale * (xmax - xmin)

                # Add the map scale for psbasemap
                sections['shell variable']['set MAP_SCALE2'] = self.gmt_scale+str(plot_width)
                new_lines.insert(index + 6, "set MAP_SCALE2      = %s\n" % (sections['shell variable']['set MAP_SCALE2']))
                          
                # Add the geographic region for psbasemap
                sections['shell variable']['set MAP_REGION2'] = self.region['geo']
                new_lines.insert(index + 8, "set MAP_REGION2     = %s\n" % (sections['shell variable']['set MAP_REGION2']))

            elif 'PAPER_MEDIA' in line:
                new_lines[index] = "gmtset PAPER_MEDIA Letter\n"
                
            elif 'Make basemap' in line:
                new_lines[index + 2] = "psbasemap -J$MAP_PROJECTION2$MAP_SCALE2 \ \n"
                new_lines[index + 3] = "        -R$MAP_REGION2 \ \n"
                new_lines[index + 4] = "        -B5m/5m \ \n"

        # Write the new cmd script
        for index in new_lines:
            new_cmd_f.write("%s" % index)
                
        new_cmd_f.close()
            
            
    def make_ps_map(self, outdir):
        """Make a Postscript map from the pre-generated NetCDF grid

        Keyword arguments:
        outdir -- directory path in which to store the map
        """
        if path.isfile(outdir+self.nc_grid_tile):
            try:
                subprocess.check_call(['which', 'mbm_grdplot'])
            except subprocess.CalledProcessError:
                print "\nCould not call mbm_grdplot! Please make sure MB-Sysem is properly installed\n."
                exit(-1)
            else:
                print "Ploting..."
                subprocess.call(["mbm_grdplot", "-I", outdir+self.nc_grid_tile, \
                                 "-O", outdir+self.ps_map_no_ext, \
                                 "-G2", "-A0.5/270/15", "-D", \
                                 "-PA4", "-V"])

            # Modify cmd script to replace basemap from Lambert to geographic
            lam2geo_carto(outdir+self.ps_map_shell, outdir+self.ps_map_lcc_shell)

            try:
                subprocess.check_call(['which', 'csh'])
            except subprocess.CalledProcessError:
                print "\nCould not call csh! Please make sure that the c-shell is properly installed\n."
                exit(-1)
            else:
                subprocess.call(["csh", outdir+self.ps_map_shell])
        else:
            print "\nError: NetCDF file %s not found!\n" % (self.nc_grid_tile)


        
                
