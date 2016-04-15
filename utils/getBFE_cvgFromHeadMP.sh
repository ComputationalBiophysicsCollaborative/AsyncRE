#!/bin/bash

#####################################################################################################
# A bash script to converge analysis of binding free energy for many copies of the same system.
#
# Junchao Xia  03/09/2014
#####################################################################################################

async_scripts=$1     # path to async scripts
folder=$2           # new folder to analyze
oldfolders=$3       # old folders
rbgn=$4            # starting replica
rend=$5              # ending replica
nbgn=$6              # starting time
nend=$7              # ending time
npnt=$8              # number points per copy
ncop=$9              # number of copies
root_path=`pwd`
echo "-------------------------------------------------------------------------------"
if [ -d $folder ]; then
   echo "$folder exists, remove the old bfe_conv.dat."
   rm -rf $folder/bfe_conv_all.dat 
else
   mkdir $folder
   for (( ir=$rbgn; ir<=$rend; ir++ ))
   do
       mkdir $folder/r$ir
   done
fi

for (( ip=1; ip<=$npnt; ip++ ))
do
   nfrq=$(( $ip*$npnt ))
   $async_scripts/mergeLBEdataFromHeadLS.sh $folder "$oldfolders" $rbgn $rend $nbgn $nend $npnt $ip $ncop 
   ntot=$(( (nend-nbgn+1)*ip*ncop ))
   cat input/asyncRE_analysis.cntl_temp | sed "s/NSTART/1/" | sed "s/NLAST/1/" | sed "s/NINTV/$ntot/" > $folder/asyncRE_analysis.cntl 
   cd $folder
   rm -rf .RData 
   python $async_scripts/asyncRE_analysis.py asyncRE_analysis.cntl  >& asyncRE_analysis.log
   cat bfe_conv.dat >> bfe_conv_all.dat 
   cd ../
done

