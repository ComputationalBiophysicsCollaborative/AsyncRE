#!/bin/bash

#####################################################################################################
# A bash script to extract related energies from impact output files.
#
# Junchao Xia  02/20/2015
#####################################################################################################

async_scripts=$1
oldfolders=$2
job_dirs=`ls -d $oldfolders`
neq=$3
nprod=$4
nskip=$5
nprnt=$6
rbgn=$7
rend=$8
ncopy=$9
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
           ${async_scripts}/getImpactOutFromShort.sh ${async_scripts} ${folder} ${folder} $neq $nprod $nskip $nprnt $rbgn $rend
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

