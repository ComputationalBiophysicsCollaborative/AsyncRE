import os,re,math,sys
import getopt
import glob


def getImpactData(file):
    if not os.path.exists(file):
        msg = 'File does not exist: %s' % file
        sys.exit(msg)
    step_line = re.compile("^ Step number:")
    number_line = re.compile("(\s+-*\d\.\d+E[\+-]\d+\s*)+")
    temperature_line = re.compile("^\s*input target temperature\s+(\d*\.*\d*)")
    have_trgtemperature = 0
    have_errtemperature = 0
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
        if have_trgtemperature == 0 and have_errtemperature == 0 : 
           print "Warning: no target temperature found in %s" % file
           have_errtemperature = 1
           #msg = "not target termperature found in " + file  
           #self.exit(msg)

        # read the step number
        if re.match(step_line, line):
            words = line.split()
            step = words[2]
            datablock = [int(step)]
            # comment out to use the instantaeous temperature 
            if have_trgtemperature == 1 :
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

basename=sys.argv[1]
neq=int(sys.argv[2])
nprod=int(sys.argv[3])
nskip=int(sys.argv[4])
nprnt=int(sys.argv[5])
cycles = []
out_files = glob.glob("%s_*.out" % basename)
# print 1,out_files
to_cycle = re.compile(basename + r"_(\d+).out")
for f in out_files:
    c = re.match(to_cycle, f).group(1)
    cycles.append(int(c))
    cycles.sort()

lbe_file=open('lbe.dat','a')
for r in cycles:
    #construct file name
    datafile = "%s_%d.out" % (basename,r)
    try:
        datai=getImpactData(datafile)	
        n=len(datai)
        nf=len(datai[0])
        for i in range(nskip,n/(neq+nprod)):
            for j in range(0,nprod,nprnt):
                k=i*(neq+nprod)+ neq + j
                tem=datai[k][1]
                tot=datai[k][3]
                pot=datai[k][5]
                lmb = datai[k][nf-4]
                u = datai[k][nf-3]
                eflat=datai[k][nf-1]
                lbe_file.write('%s\t%s\t%s\t%s\t%s\t%s\n' %(tem,tot,pot,lmb,u,eflat))

    except:
        print "Warning: Cannot open output file %s" % file

lbe_file.close()
