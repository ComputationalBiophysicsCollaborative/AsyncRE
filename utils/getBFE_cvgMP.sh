#!/bin/bash

#####################################################################################################
# A bash script to converge analysis of binding free energy for many copies of the same system.
#
# Junchao Xia  04/03/2018
#####################################################################################################

async_scripts=$1     # path to async scripts
folder=$2            # new folder to analyze
#oldfolders=$3       # old folders
oldfolders=${folder}-*     # old folders
rbgn=$3              # starting replica
rend=$4              # ending replica
nbgn=$5              # starting time
nend=$6              # ending time
neql=$7              # equilibrium time 
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

for (( ip=$nbgn; ip<=$nend; ip++ ))
do
   nfrq=$(( $ip*$npnt ))
   nhead=$(( $nfrq+$neql ))
   $async_scripts/mergeLBEdataLS.sh $folder "$oldfolders" $rbgn $rend $nhead $nfrq $ncop 
   ntot=$(( $nfrq*$ncop ))
   cat ../input/asyncRE_analysis.cntl_temp | sed "s/NSTART/1/" | sed "s/NLAST/1/" | sed "s/NINTV/$ntot/" > $folder/asyncRE_analysis.cntl 
   cd $folder
   python $async_scripts/asyncRE_analysis.py asyncRE_analysis.cntl  >& asyncRE_analysis.log
   cat bfe_conv.dat >> bfe_conv_all.dat 
   rm -rf .RData 
   cd ../
done

