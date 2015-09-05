#!/usr/bin/env python

########################################################################################################
#
# TITLE: tide_process.py
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
Run some simple processing on tide files
"""

import argparse
from sys import exit
import tide

def main():
    parser = argparse.ArgumentParser(description="Process tide data.")
    parser.add_argument('intidetype', type=str, choices=['webtide'], help='input tide format')
    parser.add_argument('intidefile', type=str, help='complete path to input tide file')
    parser.add_argument('outtidetype', type=str, choices=['mb', 'hips'], help='output tide format')
    parser.add_argument('outpath', type=str, help='path where to write the output tide file')
    args = parser.parse_args()

    # Read in the tide from specified format
    if (args.intidetype == 'webtide'):
        theTide = tide.Tide()
        theTide.load_webtide(args.intidefile)

    # Write out the tide to specified format
    if (args.outtidetype == 'mb'):
        theTide.make_mb_tide(args.outpath)
        print "The tide file %s has been written in directory %s" % (theTide.tidename+'.mbt', args.outpath)
    elif (args.outtidetype == 'hips'):
        theTide.make_hips_tide(args.outpath)
        print "The tide file %s has been written in directory %s" % (theTide.tidename+'.tid', args.outpath)

    exit(0)
        
if __name__ == '__main__':
    main()
