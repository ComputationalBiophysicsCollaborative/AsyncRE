#!/bin/bash

#####################################################################################################
# A bash script to pack impact output files.
#
# Junchao Xia  07/08/2017
#####################################################################################################

async_scripts=$1
oldfolders=$2
job_dirs=`ls -d $oldfolders`
file_types=$3
rbgn=$4
rend=$5
ncopy=$6
root_path=`pwd`
icopy=0

for folder in $job_dirs; do
    ((icopy=icopy+1))
    if ((icopy > ncopy)); then
       exit
    fi

    if [ -d $folder ]; then
        # cd $folder
        echo "working in the folder of $folder"
        ${async_scripts}/tarAndZipImpactFiles.sh ${async_scripts} ${folder} ${folder} "$file_types" $rbgn $rend
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

