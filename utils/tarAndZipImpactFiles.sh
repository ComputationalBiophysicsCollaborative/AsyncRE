#!/bin/bash

#####################################################################################################
# A bash script to tar and zip the output files of IMPACT .
#
# Junchao Xia  07/05/2017
#####################################################################################################

async_scripts=$1     #  path to scripts /home/tuf29141/software/async_scripts
job_dirs=$2          #  job folders
basename=$3          #   basename to extract .out files from IMPACT
file_types=$4        #
rbgn=$5              #  strart repplica
rend=$6              #  end replica

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
            python $async_scripts/tarAndZipImpactFiles.py $folder $file_types 
            # echo "Finished collecting data in r$ir"
            cd ../
        done
	cd $root_path
    else 
	echo "$folder does not exist."
	exit
    fi
done

 
