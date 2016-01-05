#!/bin/bash

#####################################################################################################
# A bash script to extract the binding energies for the output of IMPACT.
#
# Junchao Xia  07/28/2014
#####################################################################################################

async_scripts=$1     #  path to scripts /home/tuf29141/software/async_scripts
job_dirs=$2          #  job folders
outfile=$3           #  .out file from IMPACT
neq=$4               #  number of points from equilibrium which are removed
nprod=$5             #  number of points from production
nskip=$6             #  the first nskip MD cycles are neglected
nfreq=$7             #  the frequency to extract data from .out file
rbgn=$8              #  strart repplica
rend=$9              #  end replica

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
            python $async_scripts/getImpactOut.py $outfile $neq $nprod $nskip $nfreq
            echo "Finished collecting data in r$ir"
            cd ../
        done
	cd $root_path
    else 
	echo "$folder does not exist."
	exit
    fi
done

 
