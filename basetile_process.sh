#!/bin/bash
########################################################################################################
#
# TITLE: basetile_process.sh
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

###
# Main processing script for the creation of ArcticNet basetiles for the EM302 Amundsen dataset
#
# Required programs:
#         - MB-System version 5.4.22.20
#         - ImageMagick
###



#
# BASETILE_PROCESS_HELP() - Display some basic help about basetile_process
#
basetile_process_help() {
    bU=$(tput smul) # begin underline font
    eU=$(tput rmul) # end underline font
    bB=$(tput smso) # begin bold font
    eB=$(tput rmso) # end bold font

    printf "\nProgram basetile_process\n"
    printf "Version 1.0\n\n"
    printf "basetile_process is a high-level bash shell script used to create ArcticNet basetiles from the EM302\n"
    printf "multibeam bathymetry and backscatter data collected by the Canadian ice-breaker CCGS Amundsen.\n"
    printf "basetile_process is a front-end to MB-System and some python scripts specifically written to produce\n"
    printf "the three fundamental datasets of the Canadian Arctic Mapping program:\n"
    printf "1) 15'x30' basemap tiles in ESRI Grids (.EHdr) raster format\n"
    printf "2) 15'x30' maps in Postscript (.ps) format\n"
    printf "3) 15'x30' maps in image (.gif) format\n\n"
    printf "usage: $0 [-F[e][p][g] -G${bU}color_mode${eU} -H -R${bU}west${eU}/${bU}east${eU}/${bU}south${eU}/${bU}north${eU}]\n\n"
    printf "For a detailed description, type: ${bB}man ./basetile_process.1${eB}.\n"
}



#
# MAKE-TILES(PARAMETER) - Makes the ArcticNet basemap tiles for the specified region and product options
#
make_tiles() {
    printf "\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG

    # Make sure that datalist datalist.mb-1 is in the current directory
    if [ ! -f $DIR_ROOT/$HIGH_DATALIST ]; then
    	printf "Error! The MB-System high-level datalist $DIR_ROOT/$HIGH_DATALIST was not found!\n"
    	exit 1
    fi
    
    # Make sure that a logo file exists in the output directory
    if [ ! -f $DIR_SURFACES/logos.sun ]; then
    	cp logos.sun $DIR_SURFACES
    fi

    # Parse the creation options
    region=`echo $1 | sed 's/[epg]\{0,3\}$//g'`
    options=`echo $1 | grep -E -o [[epg]\{0,3\}$`
    if [ -z $options ]; then
	# $options is empty --> all products are wanted
	options="epg"
    fi
	
    # Call the anbasemap.py python script 
    printf "%s UTC: Making ArcticNet basemap tiles at %s m resolution with region %s and product option(s) %s.\n\n" \
	   $(date --utc +%Y%m%d-%H%M%S) $CELLSIZE $region $options | tee -a $LOG   
    python $DIR_ROOT/anbasemap.py -D $DIR_SURFACES $DIR_ROOT/$HIGH_DATALIST -- $region $options $CELLSIZE

    printf "done with make_tiles() at %s UTC.\n" $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
}

####################
# MAIN STARTS HERE #
####################

# Set the project Metadata
if [ ! -f parameters.dat ]; then
    printf "Warning! No parameter file found. Make sure that the parameters.dat file exists in the current execution directory.\n"
    exit 1
fi
chmod +x parameters.dat
source parameters.dat

# Check if log file exists. Create it if first run
if [ ! -f $LOG ]; then
    touch $LOG
fi

# Parse the command line
while getopts  ":HR:" opt
do
    case $opt in
	H)
	    # Display some help
	    basetile_process_help >&2
	    ;;
	R)
	    # Create ArcticNet Basemap tiles with parameter $OPTARG
	    make_tiles $OPTARG;
	    ;;
	\?)
	    echo "Invalid option: -$OPTARG" >&2
	    exit 1
	    ;;
	:)
	    echo "Option -$OPTARG requires an argument." >&2
	    exit 1
	    ;;
    esac

done #getopts
