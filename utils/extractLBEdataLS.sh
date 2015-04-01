#!/bin/bash

#####################################################################################################
# A bash script to extract related energies from impact output files.
#
# Junchao Xia  02/20/2015
#####################################################################################################

async_scripts=$1
oldfolders=$2
job_dirs=`ls -d $oldfolders`
rbgn=$3
rend=$4
root_path=`pwd`

for folder in $job_dirs; do
    if [ -d $folder ]; then
        # cd $folder
        echo "working in the folder of $folder"
           ${async_scripts}/getImpactOut.sh ${async_scripts} ${folder} ${folder}.out 0 1 $rbgn $rend
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

