# Clean metafiles for asynchronous Replica Exchang jobs
"""A module to remove metfiles for asynchronous RE jobs
See documentation in doc/ directory.

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
rm_type = items[1]

# get all cycle number 
cycles = []
if rm_type == "out" :
    out = "%s_*.out" % basename
    out_files = glob.glob("%s_*.out" % basename)
    print 1,out_files
    to_cycle = re.compile(basename + r"_(\d+).out")
    for f in out_files:
        c = re.match(to_cycle, f).group(1)
        cycles.append(int(c))
        cycles.sort()

#leave the last two alone
cycles.pop()
cycles.pop()

#delete .rst, .dms, and .inp files
for r in cycles:
	if rm_type == "out" :
	        #construct file name
        	rstfile = "%s_%d.rst" % (basename,r)
                outfile = "%s_%d.out" % (basename,r)
                inpfile = "%s_%d.inp" % (basename,r)
		print rstfile, outfile, inpfile
	        try:
           	    os.remove(rstfile)
        	except:
        	    print "Warning: Cannot open rst file %s" % rstfile
                try:
                    os.remove(outfile)
                except:
                    print "Warning: Cannot open out file %s" % outfile
                try:
                    os.remove(inpfile)
                except:
                    print "Warning: Cannot open inp file %s" % inpfile
 


