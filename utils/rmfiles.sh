#!/bin/bash
# remove the files in certain type  
# Contributors: 
#    Junchao Xia <junchao.xia@temple.edu>

jobname=$1
ftype=$2
rb=$3 
re=$4
for (( ir=$rb; ir<=$re; ir++ ))
do
   cd r$ir
    if [ "$ftype" = "dms" ]; then
       rm -rf  ${jobname}_lig_*.dms 
       rm -rf  ${jobname}_rcpt_*.dms       
    elif [ "$ftype" = "err" ]; then 
       rm -rf ${jobname}_*.err
    elif [ "$ftype" = "log" ]; then
       rm -rf ${jobname}_*.log
    elif [ "$ftype" = "trj" ]; then
       rm -rf ${jobname}_*.trj
    else 
       echo "need to modify script from remove $ftype files."  
    fi
   echo "finished removing $ftype files in r$ir"
   cd ../
done
