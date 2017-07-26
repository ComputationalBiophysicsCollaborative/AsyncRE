#!/bin/bash

#####################################################################################################
# A bash script to extract the macroquantities for the many output files of IMPACT .
#
# Junchao Xia  07/04/2017
#####################################################################################################

async_scripts=$1     #  path to scripts /home/tuf29141/software/async_scripts
job_dirs=$2          #  job folders
basename=$3         #   basename to extract .out files from IMPACT
neq=$4               #  number of points from equilibrium which are removed
nprod=$5             #  number of points from production
nskip=$6             #  the first nskip MD cycles are neglected
nfreq=$7             #  the frequency to extract data from .out file
rbgn=$8              #  strart repplica
rend=$9              #  end replica

root_path=`pwd`
echo "-------------------------------------------------------------------------------"
echo "|          extract related macroquantities from impact output files           |"
echo "-------------------------------------------------------------------------------"
for folder in $job_dirs; do
    if [ -d $folder ]; then
	cd $folder
	# echo "working in the folder of $folder"
        for (( ir=$rbgn; ir<=$rend; ir++ ))
        do
            cd r$ir
            # rm -rf impactOutMacQ.dat
            python $async_scripts/getImpactOutMacQ.py $basename $neq $nprod $nskip $nfreq
            # echo "Finished collecting data in r$ir"
            cd ../
        done
	cd $root_path
    else 
	echo "$folder does not exist."
	exit
    fi
done

 
