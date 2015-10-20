# Clean metafiles for asynchronous Replica Exchang jobs
"""A module to clean metfiles for asynchronous RE jobs
See documentation in doc/ directory.

Contributors: 

Junchao Xia <junchao.xia@temple.edu>
Emilio Gallicchio <emilio.gallicchio@gmail.com>

"""


import os
import sys
import math
import getopt
import re,glob
from schrodinger import structure, structureutil 

# Parse arguments
items = sys.argv[1:]
if(len(items) < 1):
    print "Please specify basename"
    sys.exit(-1)

basename = items[0]
tar_type = items[1]

# get all cycle number 
cycles = []
if tar_type == "dms" :
    dms = "%s_*.dms" % basename
    outdms_lig = basename + "_lig.tar"
    outdms_rcpt =  basename + "_rcpt.tar"
    dms_files = glob.glob("%s_lig_*.dms" % basename)
    print 1,dms_files
    to_cycle = re.compile(basename + r"_lig_(\d+).dms")
    for f in dms_files:
        c = re.match(to_cycle, f).group(1)
        cycles.append(int(c))
        cycles.sort()
elif tar_type == "rst" :
    outrst= basename + "_rst.tar"
    rst_files = glob.glob("%s_*.rst" % basename)
    print 1,rst_files
    to_cycle = re.compile(basename + r"_(\d+).rst")
    for f in rst_files:
        c = re.match(to_cycle, f).group(1)
        cycles.append(int(c))
        cycles.sort()
else:
    maeg = "%s_*.maegz" % basename
    outmae = basename + ".maegz"
    mae_files = glob.glob("%s_*.maegz" % basename)
    print 1,mae_files
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
        file_rcpt = "%s_rcpt_%d.dms" % (basename,c)
        print "dms structure files %s %s" % (file_lig,file_rcpt)
        try:
            tarcom_lig = "tar -r --file=" + outdms_lig + " " + file_lig 
            tarcom_rcpt = "tar -r --file=" + outdms_rcpt + " " + file_rcpt
            os.system(tarcom_lig)
            os.system(tarcom_rcpt)
            os.remove(file_lig)
            os.remove(file_rcpt)
        except:
            print "Warning: Cannot open dms structure file %s %s" % (file_lig, file_rcpt)

elif tar_type == "rst" :
    for c in cycles:
        #construct rst file name
        file_rst = "%s_%d.rst" % (basename,c)
        print "rst file %s" % (file_rst)
        try:
            tarcom_rst = "tar -r --file=" + outrst + " " + file_rst 
            os.system(tarcom_rst)
            os.remove(file_rst)
        except:
            print "Warning: Cannot open rst file %s" % (file_rst)

else:
    for c in cycles:
        #construct mae file name
        file = "%s_%d.maegz" % (basename,c)
        print file
        try:
            ct1 = structure.StructureReader(file).next()
            ct1.append(outmae)
            os.remove(file)
        except:
            print "Warning: Cannot open Maestro structure file %s" % file

#concatenate out files
outfile = "%s.out" % basename
fout = open(outfile,"a")
for r in cycles:
        #construct file name
        file = "%s_%d.out" % (basename,r)
        print file
        try:
            f = open(file,"r")
            fout.write( f.read() )
            f.close()
            os.remove(file)
        except:
            print "Warning: Cannot open output file %s" % file
fout.close()

#delete .rst, .dms, and .inp files
for r in cycles:
	if tar_type == "dms" :
	        #construct file name
        	rstfile = "%s_%d.rst" % (basename,r)
		print rstfile
	        try:
           	    os.remove(rstfile)
        	except:
        	    print "Warning: Cannot open rst file %s" % rstfile
	elif tar_type == "rst" :
	        file_lig = "%s_lig_%d.dms" % (basename,r)
	        file_rcpt = "%s_rcpt_%d.dms" % (basename,r)
	        inpfile = "%s_%d.inp" % (basename,r)
		print file_lig
	        print file_rcpt
	        try:
        	    os.remove(file_lig)
        	except:
	            print "Warning: Cannot open ligand dms file %s" % file_lig
       		try:
            	    os.remove(file_rcpt)
        	except:
           	    print "Warning: Cannot open receiptor dms file %s" % file_rcpt
	else : 
              #construct file name
                rstfile = "%s_%d.rst" % (basename,r)
                print rstfile
                try:
                    os.remove(rstfile)
                except:
                    print "Warning: Cannot open rst file %s" % rstfile

        inpfile = "%s_%d.inp" % (basename,r)
        print inpfile
        try:
            os.remove(inpfile)
        except:
            print "Warning: Cannot open inp file %s" % inpfile


