#!/usr/bin/env python

########################################################################################################
#
# TITLE: tide.py
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

import pandas as pd
from os import path
from datetime import datetime as dt
import numpy as np

class Tide(object):
    """Tidal signal and associated functionnalities
    """

    def __init__(self):
        """Creates an initializes a new tide object

        Keyword arguments:
        None
        """
        self.name = ""              # Original name of loaded tide file
        self.path = ""              # Original path to loaded tide file
        self.tidename = "tide_"     # Suffix for name based on tide time interval
        self.tideobs = 0            # Tide observation measurements

        
    def __repr__(self):
        """
        """
        return "Tidal variations"


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

    
    def load_webtide(self, pathname):
        """Load the tide prediction generated in HTML format by webtide

        Keyword arguments:
        pathname -- pathname to the webtide HTML file

        Returns:
        a pandas DataFrame
        """
        from lxml.html import parse

        # Store metadata
        self.name = path.basename(pathname)
        self.path = path.dirname(pathname)+'/'

        # decode the HTML file
        parsed = parse(pathname)
        doc = parsed.getroot()
        data = doc.findall('.//pre')
        header = data[0].text_content().lstrip('Columns\n').strip().split('\t')
        table = data[1].text_content().strip().split('\n')

        # Load in a DataFrame
        self.tideobs = pd.DataFrame(table)
        self.tideobs = self.tideobs[0].apply(lambda x: pd.Series(' '.join(x.split()).split(' ')))
        self.tideobs.columns = header

        # Format DataFrame to retrieve a datetime index
        ts = self.tideobs.apply(lambda x:'%s %s %s %s %s' % (x['Year'], x['Julian Day'], x['Hour'], x['Minute'], x['Second']), axis=1)
        ts = pd.to_datetime(ts, format="%Y %j %H %M %S.%f")
        self.tideobs.set_index(ts, inplace=True)
        self.tideobs.drop(['Year', 'Julian Day', 'Hour', 'Minute', 'Second'], axis=1, inplace=True)       
        
        # Add the tidename based on start and end date
        start_date = dt.strftime(self.tideobs.index[0], format="%Y-%j")
        end_date = dt.strftime(self.tideobs.index[-1], format="%Y-%j")

        # Format according to same day or range of days
        if start_date == end_date:
            self.tidename = self.tidename + start_date
        else:
            self.tidename = self.tidename + start_date + '_to_' + end_date


            
    def make_mb_tide(self, outdir='same'):
        """Write a MB-System tide file (MODE 3)

        Keyword arguments:
        outdir -- path to where the MB-System tide file should be written. Default: same location as loaded tide observations
        """
        if outdir == 'same':
            outdir = self.path

        outdir = self.__check_dir(outdir)
        pathname = outdir+self.tidename+'.mbt'
        
        out = open(pathname, 'w')

        # Write with comma separation
        self.tideobs.to_csv(out, columns=['Elevation'], header=None, date_format='%Y %j %H %M %S')
        out.close()

        # Re-read file and replace comma by space
        inn = open(pathname, 'r')
        lines = [line.replace(',', ' ') for line in inn.readlines()]
        inn.close()

        # Write final file
        out = open(pathname, 'w')        
        out.writelines(lines)
        out.close()
        

    def make_hips_tide(self, outdir='same'):
        """Write a CARIS HIPS & SIPS tide file (MODE 3)

        Keyword arguments:
        outdir -- path to where the CARIS HIPS & SIPS tide file should be written. Default: same location as loaded tide observations
        """
        if outdir == 'same':
            outdir = self.path

        outdir = self.__check_dir(outdir)
        pathname = outdir+self.tidename+'.tid'
            
        out = open(pathname, 'w')

        # Write with comma separation
        out.write('--------\n')
        self.tideobs.to_csv(out, columns=['Elevation'], header=None, date_format='%Y/%m/%d %H:%M:%S')
        out.close()

        # Re-read file and replace comma by space
        inn = open(pathname, 'r')
        lines = [line.replace(',', ' ') for line in inn.readlines()]
        inn.close()

        # Write final file
        out = open(pathname, 'w')        
        out.writelines(lines)
        out.close()
