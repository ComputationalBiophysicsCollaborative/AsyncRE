#!/bin/bash

splitpath=/home/tuf31071/wcg/hivin_16_structures/split.py

# ensure you supplied a directory
if [ -d "${1}" ]; then
  dir=${1%/}
  for subdir in `ls $dir`; do
    if [ -d "${dir}/${subdir}" ]; then
      cd $dir/$subdir
      $SCHRODINGER/run $splitpath *.maegz --snapshots snapshots --lig-fmt "${subdir}-%d_lig.maegz" --rcp-fmt "${subdir}-%d_rcp.maegz" --lig-asl "mol. 4" --rcp-asl "mol. 1-3"
      echo "Finished with ${subdir}"
      cd "../.."
    fi
  done
fi
