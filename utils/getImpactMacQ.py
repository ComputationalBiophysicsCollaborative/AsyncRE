import os,re,math,sys

inpfilename=sys.argv[1] # the *.out file from impact output
outfilename=sys.argv[2] # the output file name 

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
            #datablock = [int(step)]
            datablock = [step]

            if have_trgtemperature == 1:
               #datablock.append(float(temperature))
               datablock.append(temperature)
 
            #now read up to 3 lines of numbers
            ln = 0
            while ln < 3:
                line = f.readline()
                if not line:
                    msg = "Unexpected end of file"
                    self.exit(msg)
                if re.match(number_line, line):
                    for word in line.split():
                        #datablock.append(float(word))
                        datablock.append(word)
                    ln += 1
            data.append(datablock)
        line = f.readline()
    f.close()
    return data

datai=getImpactData(inpfilename)
n=len(datai)
nf=len(datai[0])
file=open(outfilename,'w')

for i in range(n):
    for j in range(nf) :
	file.write('%s ' %datai[i][j])	
    file.write(' \n')

file.close()
