#!/bin/bash

#####################################################################################################
# A bash script to perform convergence analysis of binding free energy for async REMD.
#
# Junchao Xia  12/08/2014
#####################################################################################################

async_scripts=$1     # path to async scripts
job_dirs=`ls -d $2`          # job folders to analyze
cntl_file=$3
ncopy=$4
root_path=`pwd`
echo "-------------------------------------------------------------------------------"
echo "|        Perform convergence analysis of binding free energy                  |"
echo "-------------------------------------------------------------------------------"
for folder in $job_dirs; do
    if [ -d $folder ]; then
        ((icopy=icopy+1))
        if ((icopy > ncopy)); then
           exit
        fi

	cd $folder
	echo "working in the folder of $folder"
          cp $cntl_file ${folder}.parm
          python $async_scripts/asyncRE_analysis.py ${folder}.parm  >& asyncRE_getConfs.log
          # mv bfe_conv_noc.dat bfe_conv_noc.dat
	echo "finished extracting conformers in $folder"
	cd $root_path
    else 
	echo "$folder does not exist."
	exit
    fi
done
