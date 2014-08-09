#!/bin/bash
##################################################################
#
# EM302 Processing Scripts
# AUTHOR: Jean-Guy Nistad
# VERSION: 8
# DATE: 2014-08-09
#
# For next commit:
#    - Corrected help display
#    - Removed the commented section about the display of unprocessed files
#    - In shiptrack, added the decoding of a complete filepath in case this is entered by the user instead of a file in the current directory.
#    - Modified the look of the parameters.dat file.
#    - Changed output from ESRI ASCII grid to ESRI grid (EHdr)
#    - shiptrack() now relies on the path to the NMEA_logger folder in the parameters.dat file
#    - in dem(), corrected a bug with the creation of the color table that made gdaldem color-relief fail.
#    - in grid(), changed the gridding algorith from Gaussian Weighted Mean to Beam Footprint
#################################################################

#
# PROCESS_ALL() - Process all .all files to generate mb59 files
#
process_all() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "%s UTC: Processing all .all files in directory %s.\n\n" $(date --utc +%Y%m%d-%H%M%S) $DIR_DATA_ALL | tee -a $LOG

    # Create the .all datalist
    printf "Creating the .all datalist." | tee -a $LOG
    ls -1 $DIR_DATA_ALL | grep '.all$' | awk '{print $1 " 058 1.000000"}' > $DIR_DATA_ALL/$DATALIST_ALL
    printf "done.\n" | tee -a $LOG

    # Create the .gsf datalist
    printf "Creating the .gsf datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_GSF | grep '.gsf$' | awk '{print $1 " 121 1.000000"}' > $DIR_DATA_GSF/$DATALIST_GSF
    printf "done.\n" | tee -a $LOG

    # Compare the listing of .all files and .gsf files.
    printf "Comparing the .all and .gsf file listing..." | tee -a $LOG
    cat $DIR_DATA_ALL/$DATALIST_ALL | awk -F '.' '{print $1}' > all_filenames
    cat $DIR_DATA_GSF/$DATALIST_GSF | awk -F '.' '{print $1}' > gsf_filenames
    # Identify the common .all and .gsf files and make a filename listing (with no extension)
    comm -12 all_filenames gsf_filenames > all_gsf_common 
    printf "done.\n" | tee -a $LOG
    
    # Identify the missing .gsf files
    comm -23 all_filenames gsf_filenames > gsf_missing
    if [ -s "gsf_missing" ]
    then
	printf "Missing .gsf file(s)! Consider editing in CARIS HIPS & SIPS and exporting a .gsf for the following files:\n" | tee -a $LOG
	cat gsf_missing | awk '{print $1 ".gsf"}' | tee -a $LOG
    fi

    # Make sure the destination directory exists. If not, create it. If yes, erase its content
    if [ ! -d $DIR_DATA_MB59 ]; then
	printf "No directory %s found. Creating it..." $DIR_DATA_MB59 | tee -a $LOG
	mkdir $DIR_DATA_MB59
    else
	printf "Cleaning the destination directory to start fresh..." | tee -a $LOG
	rm $DIR_DATA_MB59/*
	printf "done.\n" | tee -a $LOG
    fi

    # Create the merge gsf script
    printf "Creating the mbcopy script file..." | tee -a $LOG
    touch $MERGE_GSF_SCRIPT | printf "#!/bin/bash\n\n" > $MERGE_GSF_SCRIPT
    cat all_gsf_common | awk -v dir_all=$DIR_DATA_ALL -v dir_gsf=$DIR_DATA_GSF -v dir_mb59=$DIR_DATA_MB59 \
                             '{print "mbcopy -F58/59/121 -I " dir_all "/" $1 ".all -M " dir_gsf "/" $1 ".gsf -O " dir_mb59 "/" $1 ".mb59"}' >> $MERGE_GSF_SCRIPT   
    rm all_gsf_common
    printf "done.\n" | tee -a $LOG

    # run the merge gsf script
    printf "Running the mbcopy script file..." | tee -a $LOG
    chmod +x $MERGE_GSF_SCRIPT
    source $MERGE_GSF_SCRIPT
    printf "done.\n" | tee -a $LOG

    # Create the .mb59 datalist
    printf "Creating the .mb59 datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_MB59 | grep '.mb59$' | awk '{print $1 " 59 1.000000"}' > $DIR_DATA_MB59/$DATALIST_MB59
    printf "done.\n" | tee -a $LOG

    # Running mbkongsbergpreprocess on .mb59 files
    printf "Running mbkongsbergpreprocess..." | tee -a $LOG
    mbkongsbergpreprocess -C -F-1 -I $DIR_DATA_MB59/$DATALIST_MB59 | tee -a $LOG
    printf "done.\n" | tee -a $LOG

    # Remove the original mb59 files
    printf "Removing the unprocessed .mb59 files..." | tee -a $LOG
    cat $DIR_DATA_MB59/$DATALIST_MB59 | awk -v dir_mb59=$DIR_DATA_MB59 '{print "rm " dir_mb59 "/" $1}' > remove_mb59
    chmod u+x remove_mb59
    source remove_mb59
    rm remove_mb59
    printf "done.\n" | tee -a $LOG

    # Create the processed .mb59 datalist
    printf "Creating the processed .mb59 datalist..." | tee -a $LOG
    ls -1 $DIR_DATA_MB59 | grep 'f.mb59$' | awk '{print $1 " 59 1.000000"}' > $DIR_DATA_MB59/$DATALIST_MB59
    printf "done.\n" | tee -a $LOG
}

#
# GRID(MB-system datalist) - Grid the mb59 files listed in the datalist
#
grid() {
    printf "%s UTC: Gridding at %s m resolution the %s MB-System datalist.\n\n" $(date --utc +%Y%m%d-%H%M%S) $CELLSIZE $1 | tee -a $LOG
    # Make a NetCDF grid
    printf "Making an ESRI grid...\n" | tee -a $LOG
    mbgrid -A1 -I $1 -J$PROJECTION -F5 -G4 -N -V -O $DIR_SURFACES/$GRID -E$CELLSIZE/0.0/meters!
    gdal_translate -of EHdr -a_srs $PROJ_WKT $DIR_SURFACES/$GRID.asc $DIR_SURFACES/$GRID-LCC.flt
    rm $DIR_SURFACES/$GRID.asc     # Comment out for debugging
    printf "done.\n" | tee -a $LOG
}


#
# DEM() - Create a geotiff DEM using the color palette with the grid
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
# SHIPTRACK(NMEA_logger file) - Create a 5 minute decimated shiptrack from a file containing NMEA-0183 strings
#
shiptrack() {
    printf "\n\n\n" | tee -a $LOG
    printf "###########################################################################################" | tee -a $LOG
    printf "\n\n" | tee -a $LOG
    printf "UTC %s: Creating a shiptrack for the %s file.\n" $(date --utc +%Y%m%d-%H%M%S) $1 | tee -a $LOG

    # Check if the specified file exists
    if [ ! -f $NMEA/$1 ]; then
	printf "Error! The file %s was not found!\n" $1
	printf "Please check the filename or that the path %s specified in the parameters.dat file is correct.\n" $NMEA
	exit 1
    fi

    printf "Calling decode_nmea.py...\n"
    # I made a python script because if has good support for time series with the pandas library
    python decode_nmea.py $NMEA/$1
    printf "done.\n" | tee -a $LOG

    # I don't know how to retrieve the output filename of the python script, so I am parsing the input argument assuming I know what the output file looks like
    filename=$(echo $1 | awk '{print filename[(split($1,filename,"/"))]}')
    date=$(echo $1 | awk '{gsub("_NMEA.txt",""); print $1}')
    year=$(echo $date | awk '{print(substr($1,5))}')
    month=$(echo $date | awk '{print(substr($1,3,2))}')
    day=$(echo $date | awk '{print(substr($1,1,2))}')
    output_file="shiptrack"-$year$month$day".txt"
    mv $output_file $DIR_SHIPTRACK
    printf "The shiptrack file %s was created in the %s directory\n" $output_file $DIR_SHIPTRACK | tee -a $LOG
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
OPTS=`getopt -o h -l all -l grid: -l dem: -l track: -l tide-for-HIPS -l tide-for-MB -l help -- "$@"`
if [ $? != 0 ]
then
    exit 1
fi

eval set -- "$OPTS"

while true ; do
    case "$1" in
        -h) printf "Usage: $0 [--all] [--grid DATALIST] [--dem COLORTABLE] [--track NMEA_LOGGER FILE] [--tide-for-HIPS] [--tide-for-MB] [--help]\n";
	    shift;;

        --all)
	    process_all;
	    shift;;
	
	--grid)
	    grid $2;
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
	    printf "Usage: $0 [--all] [--grid DATALIST] [--dem COLORTABLE] [--track NMEA_LOGGER FILE] [--tide-for-HIPS] [tide-for-MB] [--help]\n\n"
	    printf "** DESCRIPTION:\n"
	    printf "Use the --all option to process all .all files.\n"
	    printf "Use the --grid option to grid the data from the specified MB-system datalist.\n"
	    printf "Use the --dem option to create a final dem with the specified color table. Note that the color table must have been generated by QGIS!\n"
	    printf "Use the --track option to create a shiptrack from the specified NMEA_logger file.\n"
	    printf "Use the --tide-for-HIPS option to create a CARIS HIPS & SIPS tide file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s.\n" $DIR_WEBTIDE
	    printf "Use the --tide-for-MB option to create a MB-System file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s.\n" $DIR_WEBTIDE
	    shift;;

        --) shift; break;;
    esac
done