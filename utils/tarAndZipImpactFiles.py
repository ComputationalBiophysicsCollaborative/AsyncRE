# Clean metafiles for asynchronous Replica Exchang jobs
"""A module to tar and zip result files for asynchronous RE jobs

Contributors: 

Junchao Xia <junchao.xia@temple.edu>

"""


import os
import sys
import math
import getopt
import re,glob

# Parse arguments
items = sys.argv[1:]
if(len(items) < 1):
    print "Please specify basename"
    sys.exit(-1)

basename = items[0]

file_types=items[1:]

for tar_type in file_types :

    # get all cycle number 
    cycles = []
    if tar_type == "dms" :
         dms = "%s_*.dms" % basename
         outdms_lig = basename + "_lig.tar"
         outdms_rcp =  basename + "_rcp.tar"
         dms_files = glob.glob("%s_lig_*.dms" % basename)
         # print 1,dms_files
         to_cycle = re.compile(basename + r"_lig_(\d+).dms")
         for f in dms_files:
             c = re.match(to_cycle, f).group(1)
             cycles.append(int(c))
             cycles.sort()
    if tar_type == "rst" :
         outrst= basename + "_rst.tar"
         rst_files = glob.glob("%s_*.rst" % basename)
         # print 1,rst_files
         to_cycle = re.compile(basename + r"_(\d+).rst")
         for f in rst_files:
             c = re.match(to_cycle, f).group(1)
             cycles.append(int(c))
             cycles.sort()
    if tar_type == "out" :
         outout= basename + "_out.tar"
         out_files = glob.glob("%s_*.out" % basename)
         # print 1,out_files
         to_cycle = re.compile(basename + r"_(\d+).out")
         for f in out_files:
             c = re.match(to_cycle, f).group(1)
             cycles.append(int(c))
             cycles.sort()
    if tar_type == "maegz":
         from schrodinger import structure, structureutil
         maeg = "%s_*.maegz" % basename
         outmae = basename + ".maegz"
         mae_files = glob.glob("%s_*.maegz" % basename)
         # print 1,mae_files
         to_cycle = re.compile(basename + r"_(\d+).maegz")
         for f in mae_files:
             c = re.match(to_cycle, f).group(1)
             cycles.append(int(c))
             cycles.sort()

    #leave the last two alone
    cycles.pop()
    cycles.pop()

    # concatenate mae, dms or rst to tar files
    if tar_type == "dms" :
       for c in cycles:
        #construct dms file name
           file_lig = "%s_lig_%d.dms" % (basename,c)
           file_rcp = "%s_rcp_%d.dms" % (basename,c)
           # print "dms structure files %s %s" % (file_lig,file_rcp)
           try:
              tarcom_lig = "tar -r --file=" + outdms_lig + " " + file_lig 
              tarcom_rcp = "tar -r --file=" + outdms_rcp + " " + file_rcp
              os.system(tarcom_lig)
              os.system(tarcom_rcp)
              os.remove(file_lig)
              os.remove(file_rcp)
           except:
              print "Warning: Cannot open dms structure file %s %s" % (file_lig, file_rcpt)
       os.system("gzip " + outdms_lig)
       os.system("gzip " + outdms_rcp)
    if tar_type == "rst" :
       for c in cycles:
          #construct rst file name
          file_rst = "%s_%d.rst" % (basename,c)
          # print "rst file %s" % (file_rst)
          try:
              tarcom_rst = "tar -r --file=" + outrst + " " + file_rst 
              os.system(tarcom_rst)
              os.remove(file_rst)
          except:
              print "Warning: Cannot open rst file %s" % (file_rst)
       os.system("gzip " + outrst)
    if tar_type == "out" :
       for c in cycles:
          #construct rst file name
          file_out = "%s_%d.out" % (basename,c)
          # print "out file %s" % (file_out)
          try:
              tarcom_out = "tar -r --file=" + outout + " " + file_out
              os.system(tarcom_out)
              os.remove(file_out)
          except:
              print "Warning: Cannot open out file %s" % (file_out)
          # remove corresponding inp files
          file_inp = "%s_%d.inp" % (basename,c)
          # print "inp file %s" % (file_inp)
          try:
              os.remove(file_inp)
          except:
              print "Warning: Cannot open inp file %s" % file_inp
       os.system("gzip " + outout)

    if tar_type == "maegz" :
       from schrodinger import structure, structureutil

       for c in cycles:
          #construct mae file name
          file = "%s_%d.maegz" % (basename,c)
          # print file
          try:
              ct1 = structure.StructureReader(file).next()
              ct1.append(outmae)
              os.remove(file)
          except:
              print "Warning: Cannot open Maestro structure file %s" % file


