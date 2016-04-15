#!/bin/bash

#####################################################################################################
# A bash script to cleanup and resubmit for async REMD.
#
# Junchao Xia  07/15/2014
#####################################################################################################

async_scripts=$1
job_dirs=$2
rbgn=$3
rend=$4
tar_type=$5
root_path=`pwd`

echo "-------------------------------------------------------------------------------"
echo "|                                                                             |"
echo "-------------------------------------------------------------------------------"

for folder in $job_dirs; do
    if [ -d $folder ]; then
        cd $folder
        echo "working in the folder of $folder"
          for (( ir=$rbgn;ir<=$rend; ir++ ))
	  do 
            cd r$ir 
	    tar -xvf ${folder}_${tar_type}.tar 
            cd ../
          done
        cd $root_path
    else
        echo "$folder does not exist."
        exit
    fi
done

