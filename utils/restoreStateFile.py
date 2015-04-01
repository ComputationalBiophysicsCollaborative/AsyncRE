import os
import sys
import time
import pickle
import random
import shutil
#import ast 

# input state file in txt format
inpfile=sys.argv[1]  
# output state file in pickle format
outfile=sys.argv[2]

# input file for wuid 
#wuid_file = 'cyfipmE_boinc.stat'
wuid_file = sys.argv[3]

#nreplicas = ast.literal_eval(sys.argv[4])
nreplicas = int(sys.argv[4])

# create status table
status = [{'stateid_current': k, 'running_status': 'W', 
                'cycle_current': 1} for k in range(nreplicas)]

f = open(inpfile,'r')
line = f.readline()
while line:
    words = line.split()
    if words[0] not in  ['Replica','Running', 'Waiting'] : 
       replica = int(words[0])
       stateid = int(words[1])
       r_status = words[4]
       cycle = int(words[5])
       status[replica] = {'stateid_current': stateid, 'running_status': r_status, 'cycle_current': cycle}
    line = f.readline()

print status
status_file = outfile
f = open(status_file,'w')
pickle.dump(status,f)
f.close()

#wuid_file = 'cyfipmE_boinc.stat'
replica_to_wuid = [ None for k in range(nreplicas)]
print replica_to_wuid
f = open(wuid_file,'w')
pickle.dump(replica_to_wuid,f)
f.close()


