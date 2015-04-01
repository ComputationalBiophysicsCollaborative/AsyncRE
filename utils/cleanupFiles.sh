#!/bin/bash

#####################################################################################################
# A bash script to cleanup and resubmit for async REMD.
#
# Junchao Xia  07/15/2014
#####################################################################################################

schrodinger_path=$1
async_scripts=$2
job_dirs=$3
rbgn=$4
rend=$5

root_path=`pwd`

echo "-------------------------------------------------------------------------------"
echo "|                    Cleanup and merge intermediate files.                    |"
echo "-------------------------------------------------------------------------------"

for folder in $job_dirs; do
    if [ -d $folder ]; then
        cd $folder
        echo "working in the folder of $folder"
           $async_scripts/cleanup.sh $schrodinger_path $async_scripts $folder academic $rbgn $rend
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

