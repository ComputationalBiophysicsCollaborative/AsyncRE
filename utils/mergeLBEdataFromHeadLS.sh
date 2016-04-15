#!/bin/bash

#####################################################################################################
# A bash script to merge lbe.dat from all simulated systems.
#
# Junchao Xia  03/04/2015
#####################################################################################################
newfolder=$1
oldfolders=$2
job_dirs=`ls -d $oldfolders`
rbgn=$3
rend=$4
nbgn=$5
nend=$6
npnts=$7
nincl=$8
ncopy=$9
root_path=`pwd`

if [ ! -d "$newfolder" ]; then
   mkdir $newfolder
fi

for (( ir0=$rbgn; ir0<=$rend; ir0++ ))
do
   if [ -d $newfolder/r$ir0 ]; then
      rm -rf $newfolder/r$ir0/lbe.dat
   else 
      mkdir $newfolder/r$ir0
   fi
done

for (( nstart=$nbgn; nstart<=$nend; nstart++ ))
do

  ((nhead = nstart*npnts + nincl))
  ((ntail = nincl))

   #echo "merge files from folders as $job_dirs"
   icopy=0
   for folder in $job_dirs; do
      if [ -d $folder ]; then
        ((icopy=icopy+1))
	if ((icopy > ncopy)); then
           exit  
        fi
        echo "working in the folder of $folder"
 	for (( ir=$rbgn; ir<=$rend; ir++ ))
        do
           head -n $nhead $folder/r$ir/lbe.dat | tail -n $ntail >> $newfolder/r$ir/lbe.dat 
        done
      else
        echo "$folder does not exist."
        exit
      fi
   done

done

