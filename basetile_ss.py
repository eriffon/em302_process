#!/usr/bin/env python

########################################################################################################
#
# TITLE: basetile_ss.py
# AUTHOR: Jean-Guy Nistad
# 
# Copyright (C) 2016  Jean-Guy Nistad
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
Class for basemap tile of type backscatter (sidescan)
"""

from os import path, remove
import sys
import subprocess
from basetile import Basetile


class BasetileSs(Basetile):
    """ArcticNet sidescan backscatter basemap tile and associated functionnalities"""

    

    
    def __init__(self, name, region, cellsize):
        """Creates and initialize a new amplitude backscatter basetile object

        Keyword arguments:
        name -- name of the basemap tile
        region -- geographic extent of the tile
        cellsize -- the spatial resolution of the tile
        """
        # Initialize the SuperClass
        Basetile.__init__(self, name, region, cellsize, '_Zss')


    def __str__(self):
        """print the class attributes"""

        return "ArcticNet amplitude backscatter basemap tile %s with region %s and spatial resolution %s meters" \
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

        
        
    def make_ss_grid(self, datalist, outdir):
        """Make as sidescan backscatter NetCDF grid from the specified datalist

        Keyword arguments:
        datalist -- MB-System datalist
        outdir -- directory path in which to store the grid

        Returns: a NetCDF grid
        """
        outdir = self.__check_dir(outdir)
        if not(path.isfile(datalist)):
            print "\nError: no such file %s found.\n" % (datalist)
            sys.exit(-1)
            
        # Grid
        try:
            subprocess.check_call(['which', 'mbgrid'])
        except subprocess.CalledProcessError:
            print "\nCould not call mbgrid! Please make sure MB-Sysem is properly installed\n."
            sys.exit(-1)
        else:
            print "Mosaicking with %s m cell size..." % (self.metadata['cellsize'])
            subprocess.call(["mbmosaic", "-I", datalist, \
                             "-A4", "-N", "-Y6", \
                             "-C2/2", "-F0.05", \
                             "-R"+self.metadata['region']['geo'], \
                             "-JAmundsen", \
                             "-E"+str(self.metadata['cellsize'])+"/0.0/meters!", \
                             "-O", outdir+self.nc_grid['no_ext'], "-V"])

        # Cookie cut the grid and check if there is data in end result
        if (self.cookie_cut(outdir)):
            print "No data to grid for basetile %s!\n" % (self.metadata['name'])
            
        # Remove unnecessary file(s)
        if path.isfile(outdir+self.nc_grid['cmd_script']):
            # csh grid script
            remove(outdir+self.nc_grid['cmd_script'])




    def modify_ss_ps_plot(self, outdir, org_cmd, new_cmd, logo, psviewer, display = 'False'):
        """Create a new a c-shell script based in the one generated by MB-System's mb_grdplot command to mix a geographic basemap with a projected grid

        Positional arguments:
        outdir -- directory path in which to store the c-shell script
        org_cmd -- name of the original c-shell script
        new_cmd -- name of the modified c-shell script
        logo -- logo to display in the legend
        psviewer -- the currently used ps viewer

        Kerword argument:
        display -- flag to determine if the resulting ps map should be launched upon execution (default: don't display)
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
        new_dict['shell variable']['set PS_FILE'] = "set PS_FILE         = %s\n" % (outdir+self.ps_map['lcc_map'])
        new_dict['shell variable']['set CPT_FILE'] = "set CPT_FILE        = %s\n" % (outdir+self.ps_map['lcc_cpt'])
        new_dict['shell variable']['set MAP_PROJECTION2'] = "set MAP_PROJECTION2 = L\n"
        new_dict['shell variable']['set MAP_SCALE2'] = "\n" # Will be determined dynamically when the file is read!
        new_dict['shell variable']['set MAP_REGION2'] = "set MAP_REGION2     = %s\n" % (self.metadata['region']['geo'])
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
        new_dict['Make legend']['Tilename'] = "L 8 1 L Amundsen Basemap Tile %s\n" % (self.metadata['name'])
        new_dict['Make legend']['Gap3'] = "G 0.1c\n"
        new_dict['Make legend']['Datatype_header'] = "L 8 1 L @;128/128/128;Datatype:@;;\n"
        new_dict['Make legend']['Datatype'] = "L 8 1 L Sidescan Backscatter mosaicked at 10m planimetric resolution\n"
        new_dict['Make legend']['Projection_header'] = "L 8 1 L @;128/128/128;Projection:@;;\n"
        new_dict['Make legend']['Projection'] = "L 8 1 L Lambert Conic Conformal\n"
        new_dict['Make legend']['HorizontalDatum_header'] = "L 8 1 L @;128/128/128;Horizontal Datum:@;;\n"
        new_dict['Make legend']['HorizontalDatum'] = "L 8 1 L WGS84\n"
        new_dict['Make legend']['VerticalDatum_header'] = "L 8 1 L @;128/128/128;Backscatter Source:@;;\n"
        new_dict['Make legend']['VerticalDatum'] = "L 8 1 L Kongsberg Seabed Image\n"
        new_dict['Make legend']['Gap4'] = "G -1.5c\n"
        new_dict['Make legend']['Map scale'] = "M - 72 10+u f -J$MAP_PROJECTION2$MAP_SCALE2 -R$MAP_REGION2\n"
        new_dict['Make legend']['EOF'] = "EOF\n\n"
        
        new_dict['Make basemap'] = {}
        new_dict['Make basemap']['Projection'] = "psbasemap -J$MAP_PROJECTION2$MAP_SCALE2 \\\n"
        new_dict['Make basemap']['Region'] = "        -R$MAP_REGION2 \\\n"
        new_dict['Make basemap']['Annotation'] = "        -B0.5/0.25 \\\n"

        new_dict['Run psviewer'] = {}
        new_dict['Run psviewer']['Execute'] = "%s %s &\n" % (psviewer, outdir+self.ps_map['lcc_map'])
        new_dict['Run psviewer']['Dont_Execute'] = "# %s %s &\n" % (psviewer, outdir+self.ps_map['lcc_map'])
        
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
                if (self.metadata['region']['xmin'] >= self.metadata['prim_merd']):
                    # Tile is East of prime meridian
                    xmax = float(self.metadata['region']['lr'][0])
                    xmin = float(self.metadata['region']['ul'][0])
                elif (self.metadata['region']['xmax'] <= self.prim_merd):
                    # Tile is West of prime meridian
                    xmax = float(self.metadata['region']['ur'][0])
                    xmin = float(self.metadata['region']['ll'][0])
                else:
                    print "\nError: Basetile %s is not well defined with respect to Prime Meridian.\n" % (self.metadata['name'])
                    sys.exit(-1)
                map_scale = float(old_dict['shell variable']['set MAP_SCALE'])
                plot_width = map_scale * (xmax - xmin)

                # Add the map scale for psbasemap
                new_dict['shell variable']['set MAP_SCALE2'] = "set MAP_SCALE2      = %s\n" % (self.metadata['gmt_scale']+str(plot_width))
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

            elif 'Run '+psviewer in line:
                if display == 'True':
                    new_lines[index + 2] = new_dict['Run psvewer']['Execute']
                else:
                    new_lines[index + 2] = new_dict['Run psviewer']['Dont_Execute']

        # Write the new cmd script
        for index in new_lines:
            new_cmd_f.write("%s" % index)

        org_cmd_f.close()
        new_cmd_f.close()




    def make_ss_ps_plot(self, outdir, logo, psviewer, display = 'False'):
        """Make a Postscript map from the pre-generated NetCDF grid

        Keyword arguments:
        outdir -- directory path in which to store the map
        logo -- logo to display in the legend
        psviewer -- name of the psviewer

        Kerword argument:
        display -- flag to determine if the resulting ps map should be launched upon execution (default: don't display)
        """
        outdir = self.__check_dir(outdir)
        
        if path.isfile(outdir+self.nc_grid['tile']):
            try:
                subprocess.check_call(['which', 'mbm_grdplot'])
            except subprocess.CalledProcessError:
                print "\nCould not call mbm_grdplot! Please make sure MB-Sysem is properly installed\n."
                sys.exit(-1)
            else:
                print "Ploting..."
                subprocess.call(["mbm_grdplot", "-I", outdir+self.nc_grid['tile'], \
                                 "-O", outdir+self.ps_map['no_ext'], \
                                 "-G1", "-W1/4", "-D", "-S", \
                                 "-MGDANNOT_FONT_PRIMARY/Helvetica-Bold", \
                                 "-MGDANNOT_FONT_SIZE/0.5c", \
                                 "-MGDELLIPSOID/WGS-84", \
                                 "-MGDFRAME_WIDTH/1.25p", \
                                 "-MGDBASEMAP_TYPE/plain", \
                                 "-PA", \
                                 "-V"])

            # Modify cmd script to replace basemap from Lambert to geographic
            self.modify_ss_ps_plot(outdir, outdir+self.ps_map['shell'], outdir+self.ps_map['lcc_shell'], logo, psviewer, display)

            # Run new script to generate Postscript
            try:
                subprocess.check_call(['which', 'csh'])
            except subprocess.CalledProcessError:
                print "\nCould not call csh! Please make sure that the c-shell is properly installed\n."
                sys.exit(-1)
            else:
                subprocess.call(["csh", outdir+self.ps_map['lcc_shell']])

            # Remove unnecessary file
            if path.isfile(outdir+self.ps_map['shell']):
                remove(outdir+self.ps_map['shell'])
            if path.isfile(outdir+self.nc_grid['tile_int']):
                remove(outdir+self.nc_grid['tile_int'])
