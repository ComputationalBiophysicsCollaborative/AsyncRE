#!/bin/bash

#####################################################################################################
# A bash script to perform convergence analysis of binding free energy for async REMD.
#
# Junchao Xia  12/08/2014
#####################################################################################################

async_scripts=$1     # path to async scripts
job_dirs=`ls -d $2`          # job folders to analyze
cntl_file=$3         # control file 
root_path=`pwd`
echo "-------------------------------------------------------------------------------"
echo "|        Perform convergence analysis of binding free energy                  |"
echo "-------------------------------------------------------------------------------"
for folder in $job_dirs; do
    if [ -d $folder ]; then
	cd $folder
	echo "working in the folder of $folder"
        python $async_scripts/asyncRE_analysis.py $cntl_file  >& asyncRE_analysis.log
        rm -rf .RData
        # mv bfe_conv_noc.dat bfe_conv_noc.dat
	echo "finished converge analysis"
	cd $root_path
    else 
	echo "$folder does not exist."
	exit
    fi
done

