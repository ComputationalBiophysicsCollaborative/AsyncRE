#!/bin/bash

#####################################################################################################
# A bash script to extract related energies from impact output files.
#
# Junchao Xia  02/20/2015
#####################################################################################################

async_scripts=$1
job_dirs=$2
neq=$3
nprod=$4
nskip=$5
nprnt=$6
rbgn=$7
rend=$8
root_path=`pwd`

for folder in $job_dirs; do
    if [ -d $folder ]; then
        # cd $folder
        echo "working in the folder of $folder"
           ${async_scripts}/getImpactOut.sh ${async_scripts} ${folder} ${folder}.out $neq $nprod $nskip $nprnt $rbgn $rend
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

