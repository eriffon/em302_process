#!/bin/bash
##################################################################
#
# EM302 Processing Scripts
# Jean-Guy Nistad
# 2014-07-09
#
#################################################################

#
# PROCESS_ALL() - Process all .all files to generate mb59 files
#
process_all() {
    printf "Processing all .all files in directory %s at %s UTC...\n" $DIR_DATA_ALL $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG

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

    # Identify the missing .all files
    comm -13 all_filenames gsf_filenames > all_missing
    if [ -s "all_missing" ]
    then
	printf "The following .gsf files will not be merged:\n" | tee -a $LOG
	cat all_missing | awk '{print $1 ".all"}' | tee -a $LOG
    fi
    rm gsf_missing all_missing all_filenames gsf_filenames

     # Create the merge gsf script
    printf "Creating the mbcopy script file..." | tee -a $LOG
    touch $MERGE_GSF_SCRIPT | printf "#!/bin/bash\n\n" > $MERGE_GSF_SCRIPT
    cat all_gsf_common | awk -v dir_all=$DIR_DATA_ALL -v dir_gsf=$DIR_DATA_GSF -v dir_mb59=$DIR_DATA_MB59 \
                             '{print "mbcopy -F58/59/121 -I " dir_all "/" $1 ".all -M " dir_gsf "/" $1 ".gsf -O " dir_mb59 "/" $1 ".mb59"}' >> $MERGE_GSF_SCRIPT   
    rm all_gsf_common
    printf "done.\n" | tee -a $LOG

    # Clear the content of the directory to start with an empty directory. BE CAREFUL WITH THIS COMMAND!!!!!!!
    printf "Cleaning the destination directory to start fresh..." | tee -a $LOG
    rm $DIR_DATA_MB59/*
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
# GRID() - Grid the mb59 files listed in the datalist
#
grid() {
    printf "Gridding at 10m resolution the %s MB-System datalist at %s UTC.\n" $1 $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    # Make a NetCDF grid
    printf "Making an ASCII ESRI grid...\n" | tee -a $LOG
    mbgrid -A1 -I $1 -J$PROJECTION -G4 -N -V -O $GRID -E10/0.0/meters!
    gdal_translate -of AAIGrid -a_srs omg.prf $GRID.asc $GRID-LCC.asc
    rm $GRID.asc     # Comment out for debugging
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

    printf "Making a geotiff DEM using the %s color table at %s UTC.\n" $1 $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    # Make the relief geotiff
    printf "Making a relief geotiff..."
    gdaldem color-relief $GRID-LCC.asc $1 $GRID-relief-LCC.tif -of GTiff
    printf "done.\n" | tee -a $LOG

    # Make a hillshade geoTIFF
    printf "Making a hillshade geoTIFF..." | tee -a $LOG
    gdaldem hillshade $GRID-LCC.asc $GRID-hillshade-LCC.tif -of GTiff
    printf "done.\n" | tee -a $LOG

    # Merge the relief and hillshade geoTIFF
    printf "Merging relief and hillshade..." | tee -a $LOG
    hsv_merge.py $GRID-relief-LCC.tif $GRID-hillshade-LCC.tif $GRID-dem-LCC.tif
    printf "done.\n" | tee -a $LOG

    # clean up
    rm $GRID-relief-LCC.tif $GRID-hillshade-LCC.tif
}

#
# SHIPTRACK(MB-system datalist) - Create a shiptrack from an MB-System datalist
#
shiptrack() {
    printf "Creating a shiptrack for the %s MB-System datalist at %s UTC..." $1 $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    TIMESTAMP=$(date --utc +%Y%m%d-%H%M%S).txt
    mbnavlist -F-1 -I $1 -D600 -OXYJ | awk '{$1=$1}1' > $DIR_SHIPTRACK/$SHIPTRACK_PREFIX-$TIMESTAMP
    printf "done.\n" | tee -a $LOG
    printf "The shiptrack file %s was created in the %s directory\n" $SHIPTRACK_PREFIX-$TIMESTAMP $DIR_SHIPTRACK | tee -a $LOG
}

#
# WEBTIDE2CARIS() - Convert the Webtide prediction file to a CARIS HIPS & SIPS tide file
#
webtide2caris() {
    printf "Converting the Webtide prediction file to a CARIS HIPS & SIPS tide file at %s UTC..." $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    # Check that the track prediction file exists
    if [ ! -f $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html ]; then
	printf "Warning! File Track Elevation Prediction (Time in GMT).html not found! Have you copied the output from Webtide to the %s directory?\n" $DIR_WEBTIDE  | tee -a $LOG
	exit 1
    fi

    # Rename the webtide track prediction file
    cp $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html $DIR_WEBTIDE/$WEBTIDE_NAME

    # Generate the CARIS HIPS & SIPS tide file
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
    printf "Converting the Webtide prediction file to a MB-System tide file at %s UTC..." $(date --utc +%Y%m%d-%H%M%S) | tee -a $LOG
    # Check that the track prediction file exists
    if [ ! -f $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html ]; then
	printf "Warning! File Track Elevation Prediction (Time in GMT).html not found! Have you copied the output from Webtide to the %s directory?\n" $DIR_WEBTIDE  | tee -a $LOG
	exit 1
    fi

    # Rename the webtide track prediction file
    cp $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html $DIR_WEBTIDE/$WEBTIDE_NAME

    # Generate the MB-system tide file
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
        -h) printf "Usage: $0 [--all] [--grid DATALIST] [--dem COLORTABLE] [--track DATALIST] [--tide-for-HIPS] [--tide-for-MB] [--help]\n";
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
	    printf "Usage: $0 [--all] [--grid DATALIST] [--dem COLORTABLE] [--track DATALIST] [--tide-for-HIPS] [tide-for-MB] [--help]\n\n"
	    printf "** DESCRIPTION:\n"
	    printf "Use the --all option to process all .all files.\n"
	    printf "Use the --grid option to grid the data from the specified MB-system datalist.\n"
	    printf "Use the --dem option to create a final dem with the specified color table.\n"
	    printf "Use the --track option to create a shiptrack from the specified MB-system datalist.\n"
	    printf "Use the --tide-for-HIPS option to create a CARIS HIPS & SIPS tide file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s.\n" $DIR_WEBTIDE
	    printf "Use the --tide-for-MB option to create a MB-System file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s.\n" $DIR_WEBTIDE
	    shift;;

        --) shift; break;;
    esac
done