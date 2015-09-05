#!/bin/bash
##################################################################
#
# EM302 Processing Scripts for CCGS Amundsen Data
# AUTHOR: Jean-Guy Nistad
# VERSION: 18
# DATE: 2015-04-29
#
# For next commit:
#
# Future improvements:
#    - Make the merge_edits.sh script optional if one does not process using CARIS HIPS & SIPS
#    - Add a warning message when script is run with no (or an invalid) argument
#    - Modify the way the code tries to find whether or not there is data in a tile to make the search faster!
#################################################################


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
# GRID-MAP(DATALIST) - Grid the mb59 files listed in the datalist and produce a postscript and a .gif file for each basemap tile
#
grid-map() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Making postscript and .gif GMT tilemaps at %s m resolution from the %s MB-System datalist.\n\n" $(date --utc +%Y%m%d-%H%M%S) $CELLSIZE $1 | tee -a $LOG
    
    # Make sure that a logo file exists in the output directory
    if [ ! -f $DIR_SURFACES/logos.sun ]; then
	cp logos.sun $DIR_SURFACES
    fi
    
    python $DIR_ROOT/anbasemap.py -D $DIR_SURFACES $1 $CELLSIZE 1
    printf "done.\n" | tee -a $LOG

    # Clean up (comment out for debugging)
    rm $DIR_SURFACES/*.grd.cmd
}



#
# GRID-ESRI(DATALIST) - Grid the mb59 files listed in the datalist and produce ESRI EHdr tile files in Lambert conformal conic projection
#
grid-esri() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Making ESRI EHdr tile files at %s m resolution from the %s MB-System datalist.\n\n" $(date --utc +%Y%m%d-%H%M%S) $CELLSIZE $1 | tee -a $LOG
    python $DIR_ROOT/anbasemap.py -D $DIR_SURFACES $1 $CELLSIZE 0
    printf "done.\n" | tee -a $LOG

    # Clean up (comment out for debugging)
    rm $DIR_SURFACES/*.txt
    rm $DIR_SURFACES/*.grd
    rm $DIR_SURFACES/*.cmd
    rm $DIR_SURFACES/*.flt.aux.xml
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
    else	
	printf "done.\n"
    fi

    # Generate the CARIS HIPS & SIPS tide file
    printf "Creating the CARIS HIPS & SIPS tide file...\n"
    python tide_process.py webtide $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html hips $DIR_HIPS_TIDE
    printf "done.\n" | tee -a $LOG
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
	printf "\nWarning! File Track Elevation Prediction (Time in GMT).html not found! Have you copied the output from Webtide to the %s directory?\n" $DIR_WEBTIDE  | tee -a $LOG
	exit 1
    else	
	printf "done.\n"
    fi

    # Generate the MB-System tide file
    printf "Creating the MB-System tide file...\n"
    python tide_process.py webtide $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html mb $DIR_MB_TIDE
    if [ $? -eq 0 ]; then
	printf "All operations completed successfuly.\n" | tee -a $LOG
    else
	printf "Errors were reported. See log.\n" | tee -a $LOG
    fi
}



####################
# MAIN STARTS HERE #
####################

# Set the project Metadata
if [ ! -f parameters.dat ]; then
    printf "Warning! No parameter file found: parameters.dat\n"
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
OPTS=`getopt -o h -l convert -l update -l process: -l grid-map: -l grid-esri: -l dem: -l track: -l tide-for-HIPS -l tide-for-MB -l help -- "$@"`
if [ $? != 0 ]
then
    exit 1
fi

eval set -- "$OPTS"

while true ; do
    case "$1" in
        -h) printf "Usage: $0 [--convert] [--update] [--process DATALIST] [--grid-map DATALIST] [grid-esri DATALIST] [--dem COLORTABLE] [--track NMEA_LOGGER FILE] [--tide-for-HIPS] [--tide-for-MB] [--help]\n";
	    shift;;

        --convert)
	    convert_all;
	    shift;;

	--update)
	    update_all;
	    shift;;

	--process)
	    process_mb59 $2;
	    shift 2;;

	--grid-map)
	    grid-map $2;
	    shift 2;;

	--grid-esri)
	    grid-esri $2;
	    shift 2;;

	--dem)
	    dem $2;
	    shift 2;;

	--track)
	    shiptrack $2;
	    shift 2;;

	--tide-for-HIPS)
	    webtide2caris;
	    shift;;
	
	--tide-for-MB)
	    webtide2mb;
	    shift;;

	--help) 
	    printf "Usage: $0 [--convert] [--update] [--process DATALIST] [--grid-map DATALIST] [grid-esri DATALIST] [--dem COLORTABLE] [--track NMEA_LOGGER_FILE] [--tide-for-HIPS] [tide-for-MB] [--help]\n\n"
	    printf "** DESCRIPTION:\n"
	    printf "Use the --convert option to convert all .all files.\n"
	    printf "Use the --update option to convert new .all files not yet converted.\n"
	    printf "Use the --proccess option to create processed .mb59 files from the specified MB-system datalist.\n"
	    printf "Use the --grid-map option to produce postscript and .gif GMT grid tilemap(s) from the specified MB-system datalist.\n"
	    printf "Use the --grid-esri option to produce ESRI EHdr grid(s) from the specified MB-system datalist.\n"
	    printf "Use the --dem option to create a final dem with the specified color table. Note that the color table must have been generated by QGIS!\n"
	    printf "Use the --track option to create a shiptrack from the specified NMEA_logger file.\n"
	    printf "Use the --tide-for-HIPS option to create a CARIS HIPS & SIPS tide file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s.\n" $DIR_WEBTIDE
	    printf "Use the --tide-for-MB option to create a MB-System file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s.\n" $DIR_WEBTIDE
	    shift;;

        --) shift; break;;
    esac
done

echo $ARG_GRID
