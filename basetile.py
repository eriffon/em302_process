#!/usr/bin/env python

########################################################################################################
#
# TITLE: basetile.py
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
Class for basemap tiles
"""

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
                   'cmd': '.cmd', \
                   'ps': '.ps',  \
                   'cpt': '.cpt', \
                   'int': '.int', \
                   'mb-1': '.mb-1', \
                   'aux': '.aux', \
                   'xml': '.xml', \
                   'gif': '.gif'}
    
    

    def __get_region(self, region, src_proj, dst_proj):
        """Extract all components of the region in geodesic and projected coordinates

        Keyword argument:
        region -- geographic extent of the tile
        src_proj -- inverse projection
        dst_proj -- forward projection
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
        """Creates and initialize a new basetile object

        Keyword arguments:
        name -- name of the basemap tile
        region -- geographic extent of the tile
        cellsize -- the spatial resolution of the tile
        """
        PROJ4_LCC = "+proj=lcc +lat_1=70 +lat_2=73 +lat_0=70 +lon_0=-105 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs" 
        PROJ4_GEO = "+proj=latlong +datum=WGS84"
        GMT_SCALE = "-105/70/70/73/"
        GMT_PROJ = "l"
        PRIM_MERD = -105
        
        # Instance attributes
        self.name = name
        self.region = self.__get_region(region, PROJ4_GEO, PROJ4_LCC)
        self.cellsize = cellsize
        self.proj4_proj_lcc = PROJ4_LCC
        self.proj4_proj_geo = PROJ4_GEO
        self.gmt_proj = GMT_PROJ
        self.gmt_scale = GMT_SCALE
        self.prim_merd = PRIM_MERD
        self.nc_grid_no_ext = self.name+self.__suffix['grid']
        self.nc_grid = self.nc_grid_no_ext+self.__extension['grd']
        self.nc_grid_datalist = self.nc_grid_no_ext+self.__extension['mb-1']
        self.nc_grid_mask = self.nc_grid_no_ext+self.__suffix['mask']+self.__extension['grd']
        self.nc_grid_tile = self.nc_grid_no_ext+self.__suffix['tile']+self.__extension['grd']
        self.nc_grid_tile_int = self.nc_grid_tile+self.__extension['int']
        self.nc_cmd_script = self.nc_grid+self.__extension['cmd']
        self.esri_grid = self.nc_grid_no_ext+self.__suffix['tile']+self.__extension['flt']
        self.esri_grid_xml = self.esri_grid+self.__extension['aux']+self.__extension['xml']
        self.ps_map_no_ext = self.name+self.__suffix['psmap']
        self.ps_map = self.ps_map_no_ext+self.__extension['ps']
        self.ps_map_shell = self.ps_map_no_ext+self.__extension['cmd']
        self.ps_map_lcc_no_ext = self.name+self.__suffix['psmap_lcc']
        self.ps_map_lcc = self.ps_map_lcc_no_ext+self.__extension['ps']
        self.ps_map_lcc_shell = self.ps_map_lcc_no_ext+self.__extension['cmd']
        self.ps_map_lcc_cpt = self.ps_map_lcc_no_ext+self.__extension['cpt']
        self.gif_map_lcc = self.ps_map_lcc_no_ext+self.__extension['gif']


        
        
    def __str__(self):
        """print the class attributes"""

        return "ArcticNet basemap tile %s with region %s and spatial resolution %s meters" \
            % (self.name, self.region, self.cellsize)


    def __check_dir(self, directory):
        """Check that the directory path terminates with a '/' character. Append it if necessary

        Keyword argument:
        directory -- directory path to check

        Returns:
        directory -- directory path with '/' appended
        """
        if (directory[-1] != '/'):
            directory = directory+'/'

        return directory
    
        
    def make_poly_ascii(self, outdir):
        """Generate a ascii file containing coordinates defining the tile's region

        Keyword arguments:
        outdir -- directory path in which to store the ascii file

        Returns:
        filename -- complete path to the ascii file
        """
        import pyproj
       
        # Open a file to store results
        outdir = self.__check_dir(outdir)
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

        Returns:
        status -- True when the NetCDF grid has valid data. False otherwise.
        """
        outdir = self.__check_dir(outdir)
        status = False
        
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
                             "-C2/2", \
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
            # original NetCDF grid
            remove(outdir+self.nc_grid)
            
        if path.isfile(outdir+self.nc_grid_mask):
            # NetCDF grid mask
            remove(outdir+self.nc_grid_mask)
          
        if path.isfile(outdir+self.nc_cmd_script):
            # csh grid script
            remove(outdir+self.nc_cmd_script)

        # Check if the NetCDF grid contains valid data
        try:
            subprocess.check_call(['which', 'grdinfo'])
        except subprocess.CalledProcessError:
            print "\nCould not call grdinfo! Please make sure gmt is properly installed\n."
            exit(-1)
        else:
            zrange = subprocess.check_output("grdinfo %s | grep 'z_min'"  % (outdir+self.nc_grid_tile), shell=True)
            zmin = float(zrange.split(' ')[2])
            zmax = float(zrange.split(' ')[4])
            if not((zmax == 0) and (zmin == 0)):
                # There is elevation data in the file. Set the return status to True
                status = True
            else:
                # There is no elevation data in the file. Delete the NetCDF grid and mb-1 file
                if path.isfile(outdir+self.nc_grid_tile):
                    # tiled NetCDF grid
                    remove(outdir+self.nc_grid_tile)

                if path.isfile(outdir+self.nc_grid_datalist):
                    # tiled NetCDF grid
                    remove(outdir+self.nc_grid_datalist)

        return status
                

    def make_esri_grid(self, outdir):
        """Make a ESRI grid from the pre-generated NetCDF grid

        Keyword arguments:
        outdir -- directory path in which to store the grid
        """
        outdir = self.__check_dir(outdir)
        
        if path.isfile(outdir+self.nc_grid_tile):
            # Convert NetCDF grid to ESRI Grid
            try:
                subprocess.check_call(['which', 'gdal_translate'])
            except subprocess.CalledProcessError:
                print "\nCould not call gdal_translate! Please make sure GDAL is properly installed\n."
                exit(-1)
            else:                
                subprocess.call(["gdal_translate", "-a_srs", self.proj4_proj_lcc, "-of", "EHdr", "-a_nodata", "-99999", outdir+self.nc_grid_tile, outdir+self.esri_grid])

                # Remove unnecessary files
                if path.isfile(outdir+self.esri_grid_xml):
                    remove(outdir+self.esri_grid_xml)
            
        else:
            print "\nError: NetCDF file %s not found!\n" % (self.nc_grid_tile)
            print "Run make_netcdf_grid() first.\n"
            


    def lam2geo_carto(self, outdir, org_cmd, new_cmd, logo):
        """Create a new a c-shell script based in the one generated by MB-System's mb_grdplot command to mix a geographic basemap with a projected grid

        Keyword arguments:
        outdir -- directory path in which to store the c-shell script
        org_cmd -- name of the original c-shell script
        new_cmd -- name of the modified c-shell script
        logo -- logo to display in the legend
        """
        outdir = self.__check_dir(outdir)
        
        # Open files
        org_cmd_f = open(org_cmd, 'r')
        new_cmd_f = open(new_cmd, 'w')

        # Store files in memory
        org_lines = org_cmd_f.readlines()
        new_lines = org_lines

        # Create a dict of dicts for storing lines from old script
        old_dict = {}
        
        # Create a dict of dicts for storing lines for new script
        new_dict = {}
        
        # Set some data for new script
        new_dict['shell variable'] = {}
        new_dict['shell variable']['set PS_FILE'] = "set PS_FILE         = %s\n" % (outdir+self.ps_map_lcc)
        new_dict['shell variable']['set CPT_FILE'] = "set CPT_FILE        = %s\n" % (outdir+self.ps_map_lcc_cpt)
        new_dict['shell variable']['set MAP_PROJECTION2'] = "set MAP_PROJECTION2 = L\n"
        new_dict['shell variable']['set MAP_SCALE2'] = "\n" # Will be determined dynamically when the file is read!
        new_dict['shell variable']['set MAP_REGION2'] = "set MAP_REGION2     = %s\n" % (self.region['geo'])
        new_dict['shell variable']['set Y_OFFSET'] = "\n" # Will be determined dynamically when the file is read!

        new_dict['new GMT defaults'] = {}
        new_dict['new GMT defaults']['PAPER_MEDIA'] = "gmtset PAPER_MEDIA Letter\n"

        new_dict['Make legend'] = {}
        new_dict['Make legend']['Title'] = "# Make legend\n"
        new_dict['Make legend']['pslegend'] = "\n" # Will be determined dynamically when the file is read!
        new_dict['Make legend']['Gap1'] = "G -1c\n"
        new_dict['Make legend']['Color scale'] = "B $CPT_FILE 4c 0.5c -A --ANNOT_FONT_PRIMARY=1 --ANNOT_FONT_SIZE=10 -S\n"
        new_dict['Make legend']['Image'] = "I %s 4c RT\n" % (logo)
        new_dict['Make legend']['Gap2'] = "G -2.6c\n"
        new_dict['Make legend']['Tilename_header'] = "L 8 1 L @;128/128/128;Title:@;;\n"
        new_dict['Make legend']['Tilename'] = "L 8 1 L Amundsen Basemap Tile %s\n" % (self.name)
        new_dict['Make legend']['Gap3'] = "G 0.1c\n"
        new_dict['Make legend']['Datatype_header'] = "L 8 1 L @;128/128/128;Datatype:@;;\n"
        new_dict['Make legend']['Datatype'] = "L 8 1 L Bathymetry gridded at 10m planimetric resolution\n"
        new_dict['Make legend']['Projection_header'] = "L 8 1 L @;128/128/128;Projection:@;;\n"
        new_dict['Make legend']['Projection'] = "L 8 1 L Lambert Conic Conformal\n"
        new_dict['Make legend']['HorizontalDatum_header'] = "L 8 1 L @;128/128/128;Horizontal Datum:@;;\n"
        new_dict['Make legend']['HorizontalDatum'] = "L 8 1 L WGS84(G1674)\n"
        new_dict['Make legend']['VerticalDatum_header'] = "L 8 1 L @;128/128/128;Vertical Datum:@;;\n"
        new_dict['Make legend']['VerticalDatum'] = "L 8 1 L Mean Sea Level\n"
        new_dict['Make legend']['Gap4'] = "G -1.5c\n"
        new_dict['Make legend']['Map scale'] = "M - 72 10+u f -J$MAP_PROJECTION2$MAP_SCALE2 -R$MAP_REGION2\n"
        new_dict['Make legend']['EOF'] = "EOF\n\n"
        
        new_dict['Make basemap'] = {}
        new_dict['Make basemap']['Projection'] = "psbasemap -J$MAP_PROJECTION2$MAP_SCALE2 \\\n"
        new_dict['Make basemap']['Region'] = "        -R$MAP_REGION2 \\\n"
        new_dict['Make basemap']['Annotation'] = "        -B0.5/0.25 \\\n"

        new_dict['Run evince'] = {}
        new_dict['Run evince']['Execute'] = "evince   %s &\n" % (outdir+self.ps_map_lcc)
        
        # Loop over the original file, get relevant parameters and store edits for new script      
        for index, line in enumerate(org_lines):
            
            if 'shell variables' in line:
                if not old_dict.has_key('shell variable'):
                    old_dict['shell variable'] = {}
                    # Read the 'shell variables'
                    for i in range(7):
                        (key,val) = org_lines[index + i + 1].split('=',1)
                        key = key.strip()
                        val = val.strip()
                        old_dict['shell variable'][key] = val

                # Modify the Postcript filename
                new_lines[index + 1] = new_dict['shell variable']['set PS_FILE']

                # Modify the CPT filename
                new_lines[index + 2] = new_dict['shell variable']['set CPT_FILE']

                # Add the Lambert projection for psbasemap
                new_lines.insert(index + 4, new_dict['shell variable']['set MAP_PROJECTION2'])

                # Compute the plot width of the original script
                if (self.region['xmin'] >= self.prim_merd):
                    # Tile is East of prime meridian
                    xmax = float(self.region['lr'][0])
                    xmin = float(self.region['ul'][0])
                elif (self.region['xmax'] <= self.prim_merd):
                    # Tile is West of prime meridian
                    xmax = float(self.region['ur'][0])
                    xmin = float(self.region['ll'][0])
                else:
                    print "\nError: Basetile %s is not well defined with respect to Prime Meridian.\n" % (self.name)
                    exit(-1)
                map_scale = float(old_dict['shell variable']['set MAP_SCALE'])
                plot_width = map_scale * (xmax - xmin)

                # Add the map scale for psbasemap
                new_dict['shell variable']['set MAP_SCALE2'] = "set MAP_SCALE2      = %s\n" % (self.gmt_scale+str(plot_width))
                new_lines.insert(index + 6, new_dict['shell variable']['set MAP_SCALE2'])
                          
                # Add the geographic region for psbasemap
                new_lines.insert(index + 8, new_dict['shell variable']['set MAP_REGION2'])

                # Increment the Y_OFFSET to bring the map up
                y_offset = float(old_dict['shell variable']['set Y_OFFSET'])
                new_y_offset = y_offset + 1                
                new_dict['shell variable']['set Y_OFFSET'] = "set Y_OFFSET        = %s\n" % (str(new_y_offset))
                new_lines[index + 10] = new_dict['shell variable']['set Y_OFFSET']

            elif 'PAPER_MEDIA' in line:
                new_lines[index] = new_dict['new GMT defaults']['PAPER_MEDIA']

            elif 'Make color scale' in line:
                # Remove the old color scale
                for i in range(5):
                    new_lines.pop(index + 1)

                # Add a new section title
                new_lines[index] = new_dict['Make legend']['Title']

                # Add the call to pslegend
                x_offset = float(old_dict['shell variable']['set X_OFFSET'])
                y_offset = new_y_offset
                box_x_offset = -1 * x_offset + 0.05
                box_y_offset = -1 * y_offset + 0.05
                new_dict['Make legend']['pslegend'] = "pslegend -J -R -Dx%s/%s/8.4/4c/BL -F -V -K -O<<EOF >> $PS_FILE\n" % (str(box_x_offset), str(box_y_offset))
                new_lines.insert(index + 1, new_dict['Make legend']['pslegend'])

                # Add the legend content
                new_lines.insert(index + 2, new_dict['Make legend']['Gap1'])
                new_lines.insert(index + 3, new_dict['Make legend']['Color scale'])
                new_lines.insert(index + 4, new_dict['Make legend']['Image'])
                new_lines.insert(index + 5, new_dict['Make legend']['Gap2'])
                new_lines.insert(index + 6, new_dict['Make legend']['Tilename_header'])
                new_lines.insert(index + 7, new_dict['Make legend']['Tilename'])
                new_lines.insert(index + 8, new_dict['Make legend']['Gap3'])
                new_lines.insert(index + 9, new_dict['Make legend']['Datatype_header'])
                new_lines.insert(index + 10, new_dict['Make legend']['Datatype'])
                new_lines.insert(index + 11, new_dict['Make legend']['Gap3'])
                new_lines.insert(index + 12, new_dict['Make legend']['Projection_header'])
                new_lines.insert(index + 13, new_dict['Make legend']['Projection'])
                new_lines.insert(index + 14, new_dict['Make legend']['Gap3'])
                new_lines.insert(index + 15, new_dict['Make legend']['HorizontalDatum_header'])
                new_lines.insert(index + 16, new_dict['Make legend']['HorizontalDatum'])
                new_lines.insert(index + 17, new_dict['Make legend']['Gap3'])
                new_lines.insert(index + 18, new_dict['Make legend']['VerticalDatum_header'])
                new_lines.insert(index + 19, new_dict['Make legend']['VerticalDatum'])
                new_lines.insert(index + 20, new_dict['Make legend']['Gap4'])
                new_lines.insert(index + 21, new_dict['Make legend']['Map scale'])
                new_lines.insert(index + 22, new_dict['Make legend']['EOF'])
                
            elif 'Make basemap' in line:
                new_lines[index + 2] = new_dict['Make basemap']['Projection']
                new_lines[index + 3] = new_dict['Make basemap']['Region']
                new_lines[index + 4] = new_dict['Make basemap']['Annotation']

            elif 'Run evince' in line:
                new_lines[index + 2] = new_dict['Run evince']['Execute']

        # Write the new cmd script
        for index in new_lines:
            new_cmd_f.write("%s" % index)

        org_cmd_f.close()
        new_cmd_f.close()
            
            
    def make_ps_map(self, outdir, logo):
        """Make a Postscript map from the pre-generated NetCDF grid

        Keyword arguments:
        outdir -- directory path in which to store the map
        logo -- logo to display in the legend
        """
        outdir = self.__check_dir(outdir)
        
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
                                 "-G2", "-A0.5/270/15", \
                                 "-MGDANNOT_FONT_PRIMARY/Helvetica-Bold", \
                                 "-MGDANNOT_FONT_SIZE/0.5c", \
                                 "-MGDELLIPSOID/WGS-84", \
                                 "-MGDFRAME_WIDTH/1.25p", \
                                 "-MGDBASEMAP_TYPE/plain", \
                                 "-PA", \
                                 "-V"])

            # Modify cmd script to replace basemap from Lambert to geographic
            self.lam2geo_carto(outdir, outdir+self.ps_map_shell, outdir+self.ps_map_lcc_shell, logo)

            # Run new script to generate Postscript
            try:
                subprocess.check_call(['which', 'csh'])
            except subprocess.CalledProcessError:
                print "\nCould not call csh! Please make sure that the c-shell is properly installed\n."
                exit(-1)
            else:
                subprocess.call(["csh", outdir+self.ps_map_lcc_shell])

            # Remove unnecessary file
            if path.isfile(outdir+self.ps_map_shell):
                remove(outdir+self.ps_map_shell)
            if path.isfile(outdir+self.nc_grid_tile_int):
                remove(outdir+self.nc_grid_tile_int)
                
        else:
            print "\nError: NetCDF file %s not found!\n" % (self.nc_grid_tile)
            print "Run make_netcdf_grid() first.\n"


            
    def make_gif_map(self, outdir, logo):
        """Make an image (.gif) map from the pre-generated Postscript file. Generate the Postscript if it does not exist.

        Keyword arguments:
        outdir -- directory path in which to store the map
        logo -- logo to display in the legend
        """
        outdir = self.__check_dir(outdir)
        
        if not(path.isfile(outdir+self.ps_map_lcc)):
            self.make_ps_map(outdir, logo)

        # Call ImageMagik
        try:
            subprocess.check_call(['which', 'convert'])
        except subprocess.CalledProcessError:
            print "\nCould not call convert! Please make sure ImageMagick is properly installed\n."
        else:
            subprocess.call(["convert", "-density", "240", "-flatten", outdir+self.ps_map_lcc, outdir+self.gif_map_lcc])
            

    
