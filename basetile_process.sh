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

_VERBOSE=0
WEST_LIMIT=-172
EAST_LIMIT=-44
SOUTH_LIMIT=47.5
NORTH_LIMIT=82

#
# basetile_process_help() - Display some basic help about basetile_process
#
basetile_process_help() {
    bU=$(tput smul) # begin underline font
    eU=$(tput rmul) # end underline font
    bB=$(tput smso) # begin bold font
    eB=$(tput rmso) # end bold font

    cat << EOF
Program basetile_process
Version 2.0

basetile_process is a high-level bash shell script used to create ArcticNet basetiles from the EM302
multibeam bathymetry and backscatter data collected by the Canadian ice-breaker CCGS Amundsen.
basetile_process is a front-end to MB-System and some python scripts specifically written to produce
the three fundamental datasets of the Canadian Arctic Mapping program:
    1) 15'x30' basemap tiles in ESRI Grids (.EHdr) raster format
    2) 15'x30' maps in Postscript (.ps) format
    3) 15'x30' maps in image (.gif) format

Usage: ${0##*/} -I${bU}datalist${eU} [ -A${bU}datatype${eU} -D -G${bU}gridkind${eU} -H -M${bU}mapkind${eU} -R${bU}west/east/south/north${eU} -V ]

     -A          Set the datatype to grid
     -D          Print the content of the parameters file
     -G          Set the grid kind
     -H          Display this help and exit
     -I          Datalist containing swath data to grid
     -M          Set the output map kind
     -R          Set the region of extent
     -V          Apply verbose mode for increased verbosity

For a detailed description, type: ${bB}man ./basetile_process.1${eB}
EOF
}



#
# make-tiles() $DATATYPE $GRIDKIND $DATALIST $MAPKIND $REGION - Makes the ArcticNet basemap tiles for the specified region and product options
#
make_tiles() {
    [ $_VERBOSE -eq 1 ] && printf "Verifying if the datatype is valid...\n"
    if ! [[ $1 =~ ^[1-4]+$ ]]; then
	printf "Datatype value A is not in range! Possible values are 1, 2, 3 and 4. Aborting...\n"
	exit 1
    else
	datatype=$1
    fi

    [ $_VERBOSE -eq 1 ] && printf "Verifying if the gridkind is valid...\n"
    if ! [[ $2 =~ ^[1-2]+$ ]]; then
	printf "Gridkind value G is not in range! Possible values are 1 and 2. Aborting...\n"
	exit 1
    else
	gridkind=$2
    fi
    
    [ $_VERBOSE -eq 1 ] && printf "Verifying if the user-specified datalist exists...\n"
    if [ ! -f $3 ]; then
    	printf "Error! The MB-System user-specified datalist %s was not found!\n" $3
    	exit 1
    else
	datalist=$3
    fi

    [ $_VERBOSE -eq 1 ] && printf "Verifying if the mapkind is valid...\n"
    if ! [[ $4 =~ ^[1-2]+$ ]]; then
	printf "Mapkind value M is not in range! Possible values are 1 and 2. Aborting...\n"
	exit 1
    else
	mapkind=$4
    fi

    [ $_VERBOSE -eq 1 ] && printf "Making sure that a logo file exists...\n"
    if [ ! -f $DIR_SURFACES/logos.sun ]; then
	[ $_VERBOSE -eq 1 ] && printf "Copying the logo file to the %s directory...\n" $DIR_SURFACES
    	cp logos.sun $DIR_SURFACES
    fi

    [ $_VERBOSE -eq 1 ] && printf "Verifying that the region is valid...\n"
    region=$5

    # get rid of the r postfix if lower left and upper right corner coordinates are specified
    region_no_r=$(echo $region | sed 's/[r]$//g')

    # split the region string
    read west east south north <<< $(echo $region_no_r | sed 's/\//\n/g')

    if (( $(bc <<< "$west < $WEST_LIMIT") )); then
	printf "The specified %s western boundary exceeds the %s limit. Aborting...\n" $west $WEST_LIMIT
	exit 1
    fi

    if (( $(bc <<< "$east > $EAST_LIMIT") )); then
	printf "The specified %s eastern boundary exceeds the %s limit. Aborting...\n" $east $EAST_LIMIT
	exit 1
    fi

    if (( $(bc <<< "$south < $SOUTH_LIMIT") )); then
	printf "The specified %s southern boundary exceeds the %s limit. Aborting...\n" $south $SOUTH_LIMIT
	exit 1
    fi

    if (( $(bc <<< "$north > $NORTH_LIMIT") )); then
	printf "The specified %s northern boundary exceeds the %s limit. Aborting...\n" $north $NORTH_LIMIT
	exit 1
    fi
    
    # Call the anbasemap.py python script 
    printf "\n\n%s UTC: Making ArcticNet basemap tiles from MB-System datalist %s...\n" $(date --utc +%Y%m%d-%H%M%S) $3
    python $DIR_ROOT/anbasemap.py $datalist -D $DIR_SURFACES -- $DATATYPE $GRIDKIND $MAPKIND $REGION $CELLSIZE 
    printf "\n\n%s UTC: Done Making ArcticNet basemap tiles.\n" $(date --utc +%Y%m%d-%H%M%S)
}

#
# print_parameters() - Prints the parameters.dat file
#
print_parameters() {
  if [ ! -f parameters.dat ]; then
      printf "Warning! No parameter file found. Make sure that the parameters.dat file exists in the current execution directory.\n"
      exit 1
  else
      cat parameters.dat
  fi
}

####################
# MAIN STARTS HERE #
####################

# Check if MB-System is properly installed
mbstatus=$(which mbinfo)
if [ -z $mbstatus ]; then
    printf "Could not call mbinfo! Please make sure MB-Sysem is properly installed\n"
    exit 1
fi

# Set the project Metadata
if [ ! -f parameters.dat ]; then
    printf "Warning! No parameter file found. Make sure that the parameters.dat file exists in the current execution directory.\n"
    exit 1
fi
chmod +x parameters.dat
source parameters.dat

# Default arguments
DATATYPE=2
GRIDKIND=1
MAPKIND=1

# Command flags
DATALIST_FLAG=0
REGION_FLAG=0
HELP_FLAG=0

# Parse the command line
while getopts  ":A:DG:HI:M:R:V" opt
do
    case $opt in
	A)
	    # Get the datatype to use
	    DATATYPE=$OPTARG;
	    ;;
	D)
	    # Print the parameters.dat file
	    print_parameters >&2
	    ;;
	G)
	    # Get the grid kind to use
	    GRIDKIND=$OPTARG;
	    ;;
	H)
	    # Display some help
	    HELP_FLAG=1
	    basetile_process_help >&2
	    ;;
	I)
	    # Get the datalist to grid
	    DATALIST_FLAG=1
	    DATALIST=$OPTARG;
	    ;;
	M)
	    # Get map kind to generate
	    MAPKIND=$OPTARG;
	    ;;
	R)
	    # Get the user-specified region of extent
	    REGION_FLAG=1
	    REGION=$OPTARG;
	    ;;
	V)
	    # Enable verbose output mode
	    _VERBOSE=1
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

if [ $# -eq 0 ]; then
    # No option was passed: just display a useful message
    printf "To display the help, type %s -H\n" $0
elif [ $DATALIST_FLAG -eq 1 ]; then
    if [ $REGION_FLAG -eq 0 ]; then
	printf "No region was specified. Extracting the region from the datalist...\n"
	
	extent=$(mbinfo -I $DATALIST | grep -E 'Longitude|Latitude')

	datalist_west=$(echo $extent | gawk 'BEGIN {FS = "[ \t]+"};{print $3}')
	datalist_east=$(echo $extent | gawk 'BEGIN {FS = "[ \t]+"};{print $6}')
	datalist_south=$(echo $extent | gawk 'BEGIN {FS = "[ \t]+"};{print $9}')
	datalist_north=$(echo $extent | gawk 'BEGIN {FS = "[ \t]+"};{print $12}')

	REGION="$datalist_west/$datalist_east/$datalist_south/$datalist_north"
	printf "Extracted region is %s\n" $REGION
    fi
    make_tiles $DATATYPE $GRIDKIND $DATALIST $MAPKIND $REGION
elif [ $HELP_FLAG -ne 1 ]; then
    printf "%s must be called with the -I option!\n" $0
fi
