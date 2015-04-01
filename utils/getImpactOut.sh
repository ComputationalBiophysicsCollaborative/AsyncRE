#!/bin/bash

#####################################################################################################
# A bash script to extract the binding energies for the output of IMPACT.
#
# Junchao Xia  07/28/2014
#####################################################################################################

async_scripts=$1     #  path to scripts /home/tuf29141/software/async_scripts
job_dirs=$2          #  job folders
outfile=$3           #  .out file from IMPACT
nskip=$4             #  the first nskip points are neglected
nfreq=$5             #  the frequency to extract data from .out file
rbgn=$6              #  strart repplica
rend=$7              #  end replica

root_path=`pwd`
echo "-------------------------------------------------------------------------------"
echo "|                 extract related energied from impact output files           |"
echo "-------------------------------------------------------------------------------"
for folder in $job_dirs; do
    if [ -d $folder ]; then
	cd $folder
	echo "working in the folder of $folder"
        for (( ir=$rbgn; ir<=$rend; ir++ ))
        do
            cd r$ir
            rm -rf lbe.dat
            python $async_scripts/getImpactOut.py $outfile $nskip $nfreq
            echo "Finished collecting data in r$ir"
            cd ../
        done
	cd $root_path
    else 
	echo "$folder does not exist."
	exit
    fi
done

 
