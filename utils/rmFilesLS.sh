#!/bin/bash

#####################################################################################################
# A bash script to rm intermediate files from async REMD simulation.
#
# Junchao Xia  06/09/2016
#####################################################################################################

async_scripts=$1
oldfolders=$2
job_dirs=`ls -d $oldfolders`
rbgn=$3
rend=$4
filetype=$5
root_path=`pwd`
echo "-------------------------------------------------------------------------------"
echo "|                    remove intermediate files.                               |"
echo "-------------------------------------------------------------------------------"

for folder in $job_dirs; do
    if [ -d $folder ]; then
        cd $folder
        echo "working in the folder of $folder"
           $async_scripts/rmfiles.sh $folder $filetype $rbgn $rend
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

