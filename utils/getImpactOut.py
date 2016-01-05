import os,re,math,sys

outfilename=sys.argv[1] # the output file from impact

def getImpactData(file):
    if not os.path.exists(file):
        msg = 'File does not exist: %s' % file
        sys.exit(msg)
    step_line = re.compile("^ Step number:")
    number_line = re.compile("(\s+-*\d\.\d+E[\+-]\d+\s*)+")
    temperature_line = re.compile("^\s*input target temperature\s+(\d*\.*\d*)")
    have_trgtemperature = 0
    nsamples = 0
    data = []
    f = open(file ,"r")
    line = f.readline()
    while line:
           # fast forward until we get to the line: 
            # "Step number: ... ", grab target temperature along the way
            # if it's in the input file
        while line and not re.match(step_line, line):
            if re.match(temperature_line, line):
                words = line.split()
                temperature = words[3]
                have_trgtemperature = 1
            line = f.readline()
        # read the step number
        if re.match(step_line, line):
            words = line.split()
            step = words[2]
            datablock = [int(step)]
            if have_trgtemperature == 1:
                datablock.append(float(temperature))
            #now read up to 3 lines of numbers
            ln = 0
            while ln < 3:
                line = f.readline()
                if not line:
                    msg = "Unexpected end of file"
                    self.exit(msg)
                if re.match(number_line, line):
                    for word in line.split():
                        datablock.append(float(word))
                    ln += 1
            data.append(datablock)
        line = f.readline()
    f.close()
    return data

neq=int(sys.argv[2])
nprod=int(sys.argv[3])
nskip=int(sys.argv[4])
nprnt=int(sys.argv[5])
datai=getImpactData(outfilename)
n=len(datai)
nf=len(datai[0])

print "finishreadingfile"
file=open('lbe.dat','a')
for i in range(nskip,n/(neq+nprod)):
   for j in range(0,nprod,nprnt):
       k=i*(neq+nprod)+ neq + j 
       tem=datai[k][1]
       tot=datai[k][3]
       pot=datai[k][5]
       lmb = datai[k][nf-2]
       u = datai[k][nf-1]
       file.write('%s\t%s\t%s\t%s\t%s\n' %(tem,tot,pot,lmb,u))
file.close()


#print "finishreadingfile"
#file=open('lbe.dat','a')
#
#for i in range(nskip,(n/nprnt)-1):
#    tem=datai[i*nprnt][1]
#    tot=datai[i*nprnt][3]
#    pot=datai[i*nprnt][5]
#    lmb = datai[i*nprnt][nf-2]
#    u = datai[i*nprnt][nf-1]
#    file.write('%s\t%s\t%s\t%s\t%s\n' %(tem,tot,pot,lmb,u))
#file.close()
