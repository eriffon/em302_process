#!/bin/bash
##################################################################
#
# EM302 Processing Scripts
# Jean-Guy Nistad
# 2014-07-09
#
#################################################################

#
# Process all files
#
process_all() {
    printf "Processing all .all files...\n"

    # Create the .all datalist
    find $DIR_DATA_ALL -type f -mmin +30 -printf "%f\n" | sort | grep 'Amundsen.all$' > fulllist
    mbdatalist -F-1 -I fulllist > $DIR_DATA_ALL/$DATALIST_ALL

    # Running mbkongsbergpreprocess on .all files
    mbkongsbergpreprocess -C -D $DIR_DATA_MB59 -F-1 -I $DIR_DATA_ALL/$DATALIST_ALL
    printf "Done running mbkongsbergpreprocess...\n"
}

#
# Merge all mb59 files with gsf files
#
merge_gsf() {
    printf "Merging all .gsf files...\n"

    # Create the .gsf datalist
    ls -1 $DIR_DATA_GSF | grep 'Amundsen.gsf$' | awk '{print $1 " 121 1.000000"}' > $DIR_DATA_GSF/$DATALIST_GSF
    printf "Created datalist_gsf.mb-1 successfully\n"

    # Create the merge gsf script
    touch $MERGE_GSF_SCRIPT | printf "#!/bin/bash\n\n" > $MERGE_GSF_SCRIPT
    ls -1 $DIR_DATA_GSF | grep 'Amundsen.gsf$' | awk '{sub(".gsf",""); print $1}' | \
	                                         awk -v dir_mb59=$DIR_DATA_MB59 -v dir_gsf=$DIR_DATA_GSF -v dir_mb59e=$DIR_DATA_MB59E \
                                                 '{print "mbcopy -F59/59/121 -I " dir_mb59 "/" $1 ".mb59 -M " dir_gsf "/" $1 ".gsf -O " dir_mb59e "/" $1 ".mb59"}' >> $MERGE_GSF_SCRIPT

    # run the merge gsf script
    chmod +x $MERGE_GSF_SCRIPT
    source $MERGE_GSF_SCRIPT
    printf "Done merging .gsf files\n"

    # Create the mb59e datalist
    ls -1 $DIR_DATA_MB59E | grep 'Amundsen.mb59$' | awk '{print $1 " 59 1.000000"}' > $DIR_DATA_MB59E/$DATALIST_MB59E
    printf "Created datalist_mb59.mb-1 successfully\n"

    # Create ancillary files
    mbdatalist -F-1 -I $DIR_DATA_MB59E/$DATALIST_MB59E -N
    printf "Done creating ancillary files for mb59e files\n"
}

#
# Process unprocessed .all files
#
update_process_all() {
    printf "Processing new files...\n"
   
    # Creating new unprocessed .all files datalist
    find $DIR_DATA_ALL -type f -mmin +30 -printf "%f\n" | sort | grep 'Amundsen.all$' > fulllist
    cat $DIR_DATA_ALL/$DATALIST_ALL | cut -d' ' -f1 > processedlist
    comm -13 processedlist fulllist > unprocessedlist
    if [ ! -s "unprocessedlist" ]
    then
	printf "No new files to process. Exiting...\n"
	cleanup
	exit 0
    fi
    cat unprocessedlist | awk '{print $1 " 58 1.000000"}' > $DIR_DATA_ALL/$UNPROCESSED_DATALIST_ALL
    printf "Done creating new unprocessed .all files datalist...\n"

    # Running mbkongsbergpreprocess on unprocessed .all files
    mbkongsbergpreprocess -C -D $DIR_DATA_MB59 -F-1 -I $DIR_DATA_ALL/$UNPROCESSED_DATALIST_ALL
    cat $DIR_DATA_ALL/$UNPROCESSED_DATALIST_ALL >> $DIR_DATA_ALL/$DATALIST_ALL
    rm $DIR_DATA_ALL/$UNPROCESSED_DATALIST_ALL
    printf "Done running mbkongsbergpreprocess...\n"

    # Creating a new unprocessed .mb59 files datalist
    cat unprocessedlist | awk '{sub(".all",".mb59"); print}' | awk '{print $1 " 59 1.000000"}' > $DIR_DATA_MB59/$UNPROCESSED_DATALIST_MB59
    printf "Done creating new unprocessed .mb59 files datalist...\n"
    
    # Creating a shiptrack with newly processed files
    mbnavlist -F-1 -I $DIR_DATA_MB59/$UNPROCESSED_DATALIST_MB59 -D600 -OXYJ | awk '{$1=$1}1' > $DIR_SHIPTRACK/$SHIPTRACK_PREFIX_$(date --utc +%Y%m%d-%H%M%S).txt
    printf "Done creating a shiptrack with newly processed files...\n"

    # Append unprocessed mb59 list to processed mb59 list
    cat $DIR_DATA_MB59/$UNPROCESSED_DATALIST_MB59 >> $DIR_DATA_MB59/$DATALIST_MB59

    # Clean up temporary files when done
    rm fulllist processedlist unprocessedlist
}

#
# Merge unmerged mb59 files with gsf files
#
update_merge_gsf() {
    # Creating new unmerged .gsf files datalist
    ls -1 $DIR_DATA_GSF | grep 'Amundsen.gsf$' > fulllist
    cat $DIR_DATA_GSF/$DATALIST_GSF | cut -d' ' -f1 > mergedlist
    comm -13 mergedlist fulllist > unmergedlist
    if [ ! -s "unmergedlist" ]
    then
	printf "No new files to merge. Exiting...\n"
	rm fulllist mergedlist unmergedlist
	exit 0
    fi
    cat unmergedlist | awk '{print $1 " 121 1.000000"}' > $DIR_DATA_GSF/$UNPROCESSED_DATALIST_GSF
    printf "Done creating new unmerged .gsf files datalist...\n"

    # Create the merge gsf script
    touch $MERGE_GSF_SCRIPT | printf "#!/bin/bash\n\n" > $MERGE_GSF_SCRIPT
    ls -1 $DIR_DATA_GSF | cat unmergedlist | awk '{sub(".gsf",""); print $1}' | \
	                                         awk -v dir_mb59=$DIR_DATA_MB59 -v dir_gsf=$DIR_DATA_GSF -v dir_mb59e=$DIR_DATA_MB59E \
                                                 '{print "mbcopy -F59/59/121 -I " dir_mb59 "/" $1 ".mb59 -M " dir_gsf "/" $1 ".gsf -O " dir_mb59e "/" $1 ".mb59"}' >> $MERGE_GSF_SCRIPT

    # run the merge gsf script
    chmod +x $MERGE_GSF_SCRIPT
    source $MERGE_GSF_SCRIPT
    printf "Done merging .gsf files\n"

    # Append unprocessed gsf list to processed gsf list
    cat $DIR_DATA_GSF/$UNPROCESSED_DATALIST_GSF >> $DIR_DATA_GSF/$DATALIST_GSF

    # Create the newly created mb59e datalist
    cat unmergedlist | awk '{sub(".gsf",".mb59"); print}' | awk '{print $1 " 59 1.000000"}' > $DIR_DATA_MB59E/$DATALIST_MB59E
    printf "Created datalist_mb59.mb-1 successfully\n"

    # Create ancillary files
    mbdatalist -F-1 -I $DIR_DATA_MB59E/$DATALIST_MB59E -N
    printf "Done creating ancillary files for newly created mb59e files\n"

    # Clean up temporary files when done
    rm fulllist unmergedlist mergedlist
}

#
# Create a CARIS HIPS & SIPS tide file from the webtide output
#
webtide2caris() {
    # Check that the track prediction file exists
    if [ ! -f $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html ]; then
	printf "Warning! File Track Elevation Prediction (Time in GMT).html not found! Have you copied the output from Webtide to the %s directory?\n" $DIR_WEBTIDE
	exit 1
    fi

    # Rename the webtide track prediction file
    cp $DIR_WEBTIDE/Track\ Elevation\ Prediction\ \(Time\ in\ GMT\).html $DIR_WEBTIDE/$WEBTIDE_NAME

    # Generate the CARIS HIPS & SIPS tide file
    touch tempfile | echo "--------" > tempfile
    tail -n+8 $DIR_WEBTIDE/$WEBTIDE_NAME | head -n-3 | sed '/<\/p><pre>/,/<\/pre>/ s/<\/p><pre>//g' | \
	awk '{$1=$1}1' | cut -d' ' -f1,4-8 | awk 'BEGIN {FS = OFS = " " } {print $2, $3, $4, $5, $6, $1}' | \
	awk '{cmd ="date \"+%Y/%m/%d\" -d \"$(date +%Y)-01-01 $(("$2" - 1))days\""; cmd | getline var; print var " " $3 ":" $4 ":" $5 " " $6; close(cmd)}' >> tempfile 
    awk 'BEGIN { FS = "\n"; OFS = "\r\n" } { $1 = $1; print }' tempfile > $DIR_HIPS_TIDE/$HIPS_TIDE_PREFIX_$(date --utc +%Y%m%d-%H%M%S).tid
    rm tempfile
    printf "Done creating the CARIS HIPS & SIPS file...\n"
}

# 
# Set the project Metadata
#
if [ ! -f parameters.dat ]; then
    printf "Warning! No parameter file found: parameters.dat\n"
    exit 1
fi
chmod +x parameters.dat
source parameters.dat

#
# Parse the command line
#
while getopts :agutw option
do
    case "${option}" in
	a)   verbose=true
	     quiet=
	     process_all
	     ;;
	g)   verbose=true
	     quiet=
	     merge_gsf
	     ;;
        u)   verbose=true
	     quiet=
	     update_process_all
	     ;;
        t)   verbose=true
	     quiet=
	     webtide2caris
	     ;;
        w)   verbose=true
	     quiet=
	     update_merge_gsf
	     ;;
	'?') printf "Usage: $0 [-agtuw]\n"
	     printf "Use the -a option to process all .all files.\n"
	     printf "Use the -g option to merge all gsf files with mb59 files.\n"
	     printf "Use the -t option to create a CARIS HIPS & SIPS tide file with the Webtide file Track Elevation Prediction (Time in GMT).html located in %s\n" $DIR_WEBTIDE/
	     printf "Use the -u option to process all unprocessed .all files.\n"
	     printf "Use the -w option to merge all unmerged .gsf files.\n"
	     exit 1
    esac
done

