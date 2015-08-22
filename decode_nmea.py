#!/usr/bin/env python

########################################################################################################
#
# TITLE: decode_nmea.py
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
Decode NMEA-0183 GGA strings contained in a text file (update rate 1 Hz) and produced a downsampled
(update rate 0.00167 Hz; basically, 1 value every 10 minutes) shiptrack file containing the following
 space separated columns:
                      longitude latitude year julian_day hours minutes seconds

The produced shiptrack file can then be used in Webtide in order to get a tidal track prediction.
"""

import argparse
from datetime import datetime as dt
import pandas as pd

def gga(line, date):
    """Parse position from GGA sentence

    Keyword arguments:
    line -- an NMEA sentence
    date -- julian date

    Returns:
    A dictionnary for the GGA sentence
    """
    if 'GGA' not in line:
        return None

    # Initialize the dictionary
    results = { }

    results['talker'] = line[1:3]
    results['msg'] = 'GGA'

    fields = line.split(',')

    # Time
    try:
        hours = fields[1][:2]
        min = fields[1][2:4]
        sec = fields[1][4:]

        results['timeindex'] = dt.strptime(date + ' ' + hours + ':' + min + ':' + sec, '%Y %m %d %H:%M:%S.%f')
    except:
        print 'Unexpected problem with time decoding. Ignoring the following message:'
        print line
        return None

    # Latitude
    try:
        y = int(fields[2][:2]) + float(fields[2][2:])/60.
        if fields[3] == 'S':
            y = -y
        
        results['y'] = y
    except:
        print 'Unexpected problem with latitude decoding. Ignoring the following message:'
        print line
        return None

    # Longitude
    try:
        x = int(fields[4][:3]) + float(fields[4][3:])/60.
        if fields[5] == 'W':
            x = -x

        results['x'] = x
    except:
        print 'Unexpected problem with longitude decoding. Ignoring the following message:'
        print line
        return None

    # Altitude
    try:
        results['z'] = float(fields[9])
    except:
        print 'Unexpected problem with altitude decoding. Ignoring the following message:'
        print line
        return None

    return results


def vtg(line):
    """Parse ground speed and heading from VTG sentence

    Keyword arguments:
    line -- an NMEA sentence

    Returns:
    A dictionnary for the VTG sentence
    """
    if 'VTG' not in line:
        return None

    # Initialize the dictionary
    results = { }

    fields = line.split(',')

    results['heading_true'] = float(fields[1])
    results['heading_mag'] = float(fields[3])
    results['speed_kph'] = float(fields[7])

    return results



def parse_nmea_file(filename, date):
    """Create a generator that will loop over a file

    Keyword arguments:
    filename -- name of the NMEA file
    date -- the julian date

    Returns:
    All the GGA lines in the file
    """
    strings = [ ]
    for line in open(filename):
        if 'GGA' in line:
            string = gga(line, date)
            if string != None:
                strings.append(string)

    return strings


def parse_date(filename):
    """Parse the date information from a NMEA filename

    Keyword arguments:
    filename -- name of the NMEA file

    Returns:
    A dictionary with the day, month and year metadata
    """
    results = { }

    results['day'] = filename[0:2]
    results['month'] = filename[2:4]
    results['year'] = filename[4:8]
    
    return results



def webtide_shiptrack(f, df):
    """Write and output shiptrack file for webtide

    Keyword arguments:
    f -- filename to write to
    df -- pandas DataFrame
    """
    for i in range(len(df)):
        time = df.index[i]
        timestr = time.strftime('%Y %j %H %M %S')
        f.write('%s %s %s\n' % (df.x[i], df.y[i], timestr))
        f.flush()


def main():
    parser = argparse.ArgumentParser(description="Decode NMEA-0183 data strings")
    parser.add_argument('FILEIN', action='store', help='File containing NMEA-0183 strings')
    args = parser.parse_args()

    # Assign input arguments
    # TODO: check that the file exists!
    filein = args.FILEIN

    # Remove any lead slashes
    filepath = filein.split('/')
    filename = filepath[len(filepath) - 1]

    # Get the day from the filename and convert to julian
    parsed_date = parse_date(filename)
    date = parsed_date['year'] + " " + parsed_date['month'] + " " + parsed_date['day']

    # Parse the file and return a list of dictionaries
    parsed_data = parse_nmea_file(filein, date)

    # Make a Dataframe and reindex with timeindex
    df_parsed_data = pd.DataFrame(parsed_data)
    df_parsed_data.set_index('timeindex', inplace=True)

    # Resample to 10 minute intervals
    df_parsed_data_resamp = df_parsed_data.resample('5Min')

    # Create a shiptrack file
    fileout = 'shiptrack-' + parsed_date['year'] + parsed_date['month'] + parsed_date['day'] + '.txt'
    f = open(fileout, 'w')
    webtide_shiptrack(f, df_parsed_data_resamp)
    f.close()

    print fileout

if __name__ == '__main__':
    main()

