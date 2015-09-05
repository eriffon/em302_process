#!/bin/bash
########################################################################################################
#
# TITLE: em302_process.sh
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
# Main processing script for the Kongsberg EM302 multibeam data on board CCGS Amundsen Data
#
# Required programs:
#         - MB-System version 5.4.22.20
#         - ImageMagick
###

#
# MERGE_EDITS() - Merge edits from .gsf files produced from CARIS HIPS & SIPS
#
merge_edits() {
    # Create the .gsf datalist produced from CARIS HIPS & SIPS
    printf "Creating the .gsf datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_GSF | grep '.gsf$' | awk '{print $1 " 121 1.000000"}' > $DIR_DATA_GSF/$DATALIST_GSF
    printf "done.\n" | tee -a $LOG

    # Compare the listing of .mb59 files and .gsf files
    printf "Comparing the .mb59 and .gsf file listing..." | tee -a $LOG
    cat $DIR_DATA_MB59/$1 | awk -F '.' '{print $1}' > mb59_filenames
    cat $DIR_DATA_GSF/$DATALIST_GSF | awk -F '.' '{print $1}' > gsf_filenames
    
    # Identify the common .mb59 and .gsf files and make a filename listing (with no extension)
    comm -12 mb59_filenames gsf_filenames > mb59_gsf_common 
    printf "done.\n" | tee -a $LOG
    
    # Identify the missing .gsf files
    comm -23 mb59_filenames gsf_filenames > gsf_missing
    if [ -s "gsf_missing" ]
    then
	printf "Missing .gsf file(s)! Consider editing in CARIS HIPS & SIPS and exporting a .gsf for the following files:\n" | tee -a $LOG
	cat gsf_missing | awk '{print $1 ".gsf"}' | tee -a $LOG
    fi

    # Create the make esf script
    printf "Creating the script to make .esf files..." | tee -a $LOG
    touch $MAKE_ESF_SCRIPT | printf "#!/bin/bash\n\n" > $MAKE_ESF_SCRIPT
    cat mb59_gsf_common | awk -v dir_mb59=$DIR_DATA_MB59 -v dir_gsf=$DIR_DATA_GSF \
                              '{print "mbgetesf -F121 -I " dir_gsf "/" $1 ".gsf -O " dir_mb59 "/" $1 ".mb59.esf"}' >> $MAKE_ESF_SCRIPT
    printf "done.\n" | tee -a $LOG

    # run the make esf script
    printf "Running the script to make esf files..." | tee -a $LOG
    chmod +x $MAKE_ESF_SCRIPT
    source $MAKE_ESF_SCRIPT
    printf "done.\n" | tee -a $LOG

    # Clean up the temporary listings
    rm mb59_filenames gsf_filenames gsf_missing mb59_gsf_common

    # Remove the make esf script
    rm $MAKE_ESF_SCRIPT
}


#
# CONVERT_ALL() - Convert all .all files to generate mb59 files
#
convert_all() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Converting all .all files in directory %s.\n\n" $(date --utc +%Y%m%d-%H%M%S) $DIR_DATA_ALL | tee -a $LOG

    # Create the .all datalist
    printf "Creating the .all datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_ALL | grep '.all$' | grep -v '9999' | awk '{print $1 " 058 1.000000"}' > $DIR_DATA_ALL/$DATALIST_ALL
    printf "done.\n" | tee -a $LOG

    # Make sure the .mb59 destination directory exists. If not, create it. If yes, erase its content
    if [ ! -d $DIR_DATA_MB59 ]; then
	printf "No directory %s found. Creating it..." $DIR_DATA_MB59 | tee -a $LOG
	mkdir $DIR_DATA_MB59
	printf "done.\n" | tee -a $LOG
    else
	printf "Cleaning the destination directory to start fresh..." | tee -a $LOG
	rm $DIR_DATA_MB59/*
	printf "done.\n" | tee -a $LOG
    fi

    # Preprocess the .all files and create unprocessed .mb59 files
    printf "Running mbkongsbergpreprocess..." | tee -a $LOG
    mbkongsbergpreprocess -C -F-1 -I $DIR_DATA_ALL/$DATALIST_ALL -D $DIR_DATA_MB59 | tee -a $LOG
    printf "done.\n" | tee -a $LOG

    # Create the datalist for unprocessed .mb59
    printf "Creating the .mb59 datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_MB59 | grep '.mb59$' | awk '{print $1 " 59 1.000000"}' > $DIR_DATA_MB59/$DATALIST_MB59
    printf "done.\n" | tee -a $LOG

    # Merge edits from CARIS HIPS & SIPS
    merge_edits $DATALIST_MB59
}


#
# UPDATE_ALL() - Convert new .all files not yet converted to mb59 files
#
update_all() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Converting new .all files in directory %s.\n\n" $(date --utc +%Y%m%d-%H%M%S) $DIR_DATA_ALL | tee -a $LOG

    # Create the .all datalist
    printf "Creating the .all datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_ALL | grep '.all$' | grep -v '9999' | awk '{print $1 " 058 1.000000"}' > $DIR_DATA_ALL/$DATALIST_ALL
    printf "done.\n" | tee -a $LOG

    # Make sure the .mb59 destination directory exists. If not, abort. If yes, create the .mb59 datalist
    if [ ! -d $DIR_DATA_MB59 ]; then
	printf "No directory %s found!\nABORTING.\nConsider running the --convert option instead!\n" $DIR_DATA_MB59 | tee -a $LOG
    else
	# Compare the listing of .all files and .mb59 files
	printf "Comparing the .all and .mb59 file listing..." | tee -a $LOG
	cat $DIR_DATA_ALL/$DATALIST_ALL | awk -F '.' '{print $1}' > all_filenames
	cat $DIR_DATA_MB59/$DATALIST_MB59 | awk -F '.' '{print $1}' > mb59_filenames
	printf "done.\n" | tee -a $LOG

	# Identify the missing .mb59 files
	comm -23 --nocheck-order all_filenames mb59_filenames > mb59_missing
	printf "The following .all files have not been converted:\n" | tee -a $LOG
	cat mb59_missing | awk '{print $1 ".all"}' | tee -a $LOG
	printf "They will now be processed.\n" | tee -a $LOG
	
	# Create a temporary .all update datalist
	printf "Creating the temporary update .all datalist...\n" | tee -a $LOG
	cat mb59_missing | awk '{print $1 ".all 58 1.000000"}' > $DIR_DATA_ALL/$DATALIST_UPDATE_ALL
	printf "done.\n" | tee -a $LOG

	# Preprocess the .all files and create unprocessed .mb59 files
	printf "Running mbkongsbergpreprocess..." | tee -a $LOG
	mbkongsbergpreprocess -C -F-1 -I $DIR_DATA_ALL/$DATALIST_UPDATE_ALL -D $DIR_DATA_MB59 | tee -a $LOG
	printf "done.\n" | tee -a $LOG

	# Create a temporary datalist for unprocessed .mb59
	printf "Creating the temporary update .mb59 datalist..." | tee -a $LOG
	cat mb59_missing | awk '{print $1 ".mb59 59 1.000000"}' > $DIR_DATA_MB59/$DATALIST_UPDATE_MB59
	printf "done.\n" | tee -a $LOG

	# Clean up
	rm all_filenames mb59_filenames mb59_missing

	# Merge edits from CARIS HIPS & SIPS
	merge_edits $DATALIST_UPDATE_MB59

	# Update the unprocessed .mb59 datalist
	ls -1 $DIR_DATA_MB59/$DATALIST_MB59 $DIR_DATA_MB59/$DATALIST_UPDATE_MB59 | xargs cat >> $DIR_DATA_MB59/$DATALIST_MB59

	# Remove the update .all and .mb59 datalists
	rm $DIR_DATA_ALL/$DATALIST_UPDATE_ALL
	rm $DIR_DATA_MB59/$DATALIST_UPDATE_MB59
    fi

    
}


#
# PROCESS_MB59(DATALIST) - Create processed .mb59 files from the specified MB-system datalist
#
process_mb59() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Processing the mb59 files in the %s MB-System datalist.\n\n" $(date --utc +%Y%m%d-%H%M%S) $1 | tee -a $LOG
    
    # Apply the bathymetric edits
    printf "Applying bathymetric edits...\n" | tee -a $LOG
    cat $1 | awk -F '.' '{print $1}' > mb59_filenames
    touch mbset.sh | printf "#!/bin/bash\n\n" > mbset.sh
    cat mb59_filenames | awk -v dir_mb59=$DIR_DATA_MB59 '{print "mbset -PEDITSAVEMODE:1 -PEDITSAVEFILE:" dir_mb59 "/" $1 ".mb59.esf -I " dir_mb59 "/" $1 ".mb59"}' >> mbset.sh
    chmod +x mbset.sh
    source mbset.sh
    printf "...Done applying bathymetric edits.\n" | tee -a $LOG
    
    # Apply the tide
    
    # Process the mb59 files and create processed .mb59 files
    # printf "Creating processed .mb59 files..." | tee -a $LOG
    mbprocess -I $DIR_DATA_MB59/$DATALIST_MB59
    # printf "...Done creating the processed mb59 files.\n" | tee -a $LOG
   
    # Create the mb59 datalist of processed mb59 files
    printf "Creating the processed .mb59 datalist..." | tee -a $LOG
    printf "\$PROCESSED\n%s\n" $DATALIST_MB59 > $DIR_DATA_MB59/$DATALISTP_MB59
    printf "done.\n" | tee -a $LOG

    # Cleanup
    rm mbset.sh
    rm mb59_filenames
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




#
# DEM(COLORTABLE) - Create a geotiff DEM using the color palette with the grid
#
dem() {
    # Create a color table from the min max of the grid
    # TODO: Find a way to create a color table automatically
    # min=$(gdalinfo surface_10m-LCC.asc | grep 'Min=' | awk '{gsub("Min=",""); print $1}')
    # max=$(gdalinfo surface_10m-LCC.asc | grep 'Max=' | awk '{gsub("Min=",""); print $2}')

    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Making a geotiff DEM using the %s color table.\n\n" $(date --utc +%Y%m%d-%H%M%S) $1 | tee -a $LOG
    # Edit the color table for MB-System
    printf "Editing the %s color table to make it compatible for MB-System..." $1 | tee -a $LOG
    tail -n +3 $1 > mbcolortable
    cat >> mbcolortable << EOF
nv,255,255,255,255
EOF
    printf "done.\n"

    # Make the relief geotiff
    printf "Making a relief geotiff..."
    gdaldem color-relief $DIR_SURFACES/$GRID-LCC.flt mbcolortable $DIR_SURFACES/$GRID-relief-LCC.tif -of GTiff
    printf "done.\n" | tee -a $LOG

    # Make a hillshade geoTIFF (3x vertical exaggeration)
    printf "Making a hillshade geoTIFF..." | tee -a $LOG
    gdaldem hillshade $DIR_SURFACES/$GRID-LCC.flt $DIR_SURFACES/$GRID-hillshade-LCC.tif -z 3 -of GTiff
    printf "done.\n" | tee -a $LOG

    # Merge the relief and hillshade geoTIFF
    printf "Merging relief and hillshade..." | tee -a $LOG
    hsv_merge.py $DIR_SURFACES/$GRID-relief-LCC.tif $DIR_SURFACES/$GRID-hillshade-LCC.tif $DIR_SURFACES/$GRID-dem-LCC.tif
    printf "done.\n" | tee -a $LOG

    # clean up
    rm $DIR_SURFACES/$GRID-relief-LCC.tif $DIR_SURFACES/$GRID-hillshade-LCC.tif mbcolortable
}


#
# SHIPTRACK(NMEA_LOGGER_FILE) - Create a 5 minute decimated shiptrack from a file containing NMEA-0183 strings
#
shiptrack() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "UTC %s: Creating a shiptrack for the %s file.\n" $(date --utc +%Y%m%d-%H%M%S) $1 | tee -a $LOG

    # Parse the input argument to remove the path is the user added it manually
    filename=$(echo $1 | awk '{print filename[(split($1,filename,"/"))]}')
    
    # Check if the specified file exists
    if [ ! -f $NMEA/$filename ]; then
	printf "Error! The file %s was not found!\n" $1
	printf "Please check the filename or that the path %s specified in the parameters.dat file is correct.\n" $NMEA
	exit 1
    fi

    # Call the python decode_nmea file, capture the created file name and move the file to the proper directory
    printf "Calling decode_nmea.py...\n"
    shiptrack_filename=$(python decode_nmea.py $NMEA/$filename)
    printf "done.\n" | tee -a $LOG
    mv $shiptrack_filename $DIR_SHIPTRACK
    printf "The shiptrack file %s was created in the %s directory\n" $shiptrack_filename $DIR_SHIPTRACK | tee -a $LOG
}


#
# WEBTIDE2CARIS() - Convert the Webtide prediction file to a CARIS HIPS & SIPS tide file
#
webtide2caris() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Converting the Webtide prediction file to a CARIS HIPS & SIPS tide file.\n\n" $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    # Check that the track prediction file exists
    printf "Checking that the Webtide file has been generated..."
    if [ ! -f $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html ]; then
	printf "\nWarning! File Track Elevation Prediction (Time in GMT).html not found! Have you copied the output from Webtide to the %s directory?\n" $DIR_WEBTIDE  | tee -a $LOG
	exit 1
    fi
    printf "done.\n"

    # Rename the webtide track prediction file
    cp $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html $DIR_WEBTIDE/$WEBTIDE_NAME

    # Generate the CARIS HIPS & SIPS tide file
    printf "Creating the CARIS HIPS & SIPS tide file..."
    touch tempfile | echo "--------" > tempfile
    TIMESTAMP=$(date --utc +%Y%m%d-%H%M%S).tid
    tail -n+8 $DIR_WEBTIDE/$WEBTIDE_NAME | head -n-3 | sed '/<\/p><pre>/,/<\/pre>/ s/<\/p><pre>//g' | \
	awk '{$1=$1}1' | cut -d' ' -f1,4-8 | awk 'BEGIN {FS = OFS = " " } {print $2, $3, $4, $5, $6, $1}' | \
	awk '{cmd ="date \"+%Y/%m/%d\" -d \"$(date +%Y)-01-01 $(("$2" - 1))days\""; cmd | getline var; print var " " $3 ":" $4 ":" $5 " " $6; close(cmd)}' >> tempfile 
    awk 'BEGIN { FS = "\n"; OFS = "\r\n" } { $1 = $1; print }' tempfile > $DIR_HIPS_TIDE/$HIPS_TIDE_PREFIX-$TIMESTAMP
    rm tempfile
    rm $DIR_WEBTIDE/$WEBTIDE_NAME
    printf "done.\n" | tee -a $LOG
    printf "The CARIS HIPS & SIPS file %s was created in the %s directory\n" $HIPS_TIDE_PREFIX-$TIMESTAMP $DIR_HIPS_TIDE | tee -a $LOG
}


#
# WEBTIDE2MB() - Convert the Webtide prediction file to a MB-System tide file
#
webtide2mb() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Converting the Webtide prediction file to a MB-System tide file\n\n" $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    # Check that the track prediction file exists
    printf "Checking that the Webtide file has been generated..."
    if [ ! -f $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html ]; then
	printf "Warning! File Track Elevation Prediction (Time in GMT).html not found! Have you copied the output from Webtide to the %s directory?\n" $DIR_WEBTIDE  | tee -a $LOG
	exit 1
    fi
    printf "done.\n"

    # Rename the webtide track prediction file
    cp $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html $DIR_WEBTIDE/$WEBTIDE_NAME

    # Generate the MB-system tide file
    printf "Creating the MB-System tide file..."
    TIMESTAMP=$(date --utc +%Y%m%d-%H%M%S).mbt
    tail -n+8 $DIR_WEBTIDE/$WEBTIDE_NAME | head -n-3 | sed '/<\/p><pre>/,/<\/pre>/ s/<\/p><pre>//g' | \
	awk '{$1=$1}1' | cut -d' ' -f1,4-8 | awk 'BEGIN {FS = OFS = " " } {print $2, $3, $4, $5, $6, $1}' >> $DIR_MB_TIDE/$MB_TIDE_PREFIX-$TIMESTAMP
    rm $DIR_WEBTIDE/$WEBTIDE_NAME
    printf "done.\n" | tee -a $LOG
    printf "The MB-System tide file %s was created in the %s directory\n" $MB_TIDE_PREFIX-$TIMESTAMP $DIR_HIPS_TIDE | tee -a $LOG
}



#
# EM302_PROCESS_HELP() - Display some basic help about em302_process
#
em302_process_help() {
    bU=$(tput smul) # begin underline font
    eU=$(tput rmul) # end underline font
    bB=$(tput smso) # begin bold font
    eB=$(tput rmso) # end bold font

    printf "\nProgram em302_process\n"
    printf "Version 1.0\n\n"
    printf "em302_process is a high-level bash shell script used to process EM302 multibeam bathymetry data\n"
    printf "collected by the Canadian ice-breaker CCGS Amundsen. em302_process is a front-end to MB-System\n"
    printf "and some python scripts specifically written to produce the three fundamental datasets of the Canadian\n"
    printf "Arctic Mapping program: 15'x30' basemap tiles in ESRI Grids (.EHdr) raster format, 15'x30' maps in\n"
    printf "Postscript and GIF formats.\n\n"
    printf "usage: $0 [-A -B -C -D${bU}colortable${eU} -H -P${bU}datalist${eU} -S${bU}nmeafile${eU} -T${bU}west${eU}/${bU}east${eU}/${bU}south${eU}/${bU}north${eU}[e][p][g] -U]\n\n"
    printf "For a detailed description, type: ${bB}man ./em302_process.1${eB}.\n"
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

# Check if the projection WKT file exists. Create it if first run
if [ ! -f $PROJ_WKT ]; then
    touch $PROJ_WKT
    cat > $PROJ_WKT << EOF
PROJCS["Amundsen Expeditions",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0],
        UNIT["degree",0.0174532925199433],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Lambert_Conformal_Conic_2SP"],
    PARAMETER["standard_parallel_1",70],
    PARAMETER["standard_parallel_2",73],
    PARAMETER["latitude_of_origin",70],
    PARAMETER["central_meridian",-105],
    PARAMETER["false_easting",2000000],
    PARAMETER["false_northing",2000000],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]]]
EOF
fi

# Parse the command line
while getopts  ":ABCD:HP:T:S:U" opt
do
    case $opt in
	A)
	    echo "Create a MB-System tide file" >&2
	    webtide2mb;
	    ;;
	B)
	    echo "Create a CARIS HIPS & SIPS tide file" >&2
	    webtide2caris
	    ;;
	C)
	    echo "Convert all .all files" >&2
	    convert_all;
	    ;;
	D)
	    echo "Create a DEM with color table $OPTARG" >&2
	    dem $OPTARG;
	    ;;
	H)
	    # Display some help
	    em302_process_help >&2
	    ;;
	P)
	    echo "Process .mb59 files from datalist $OPTARG" >&2
	    process_mb59 $OPTARG;
	    ;;
	S)
	    echo "Create a shiptrack from the NMEA_Logger file $OPTARG" >&2
	    shiptrack $OPTARG;
	    ;;
	T)
	    # Create ArcticNet Basemap tiles with parameter $OPTARG
	    make_tiles $OPTARG;
	    ;;	
	U)
	    echo "Convert only new .all files since last conversion" >&2
	    update_all;
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
