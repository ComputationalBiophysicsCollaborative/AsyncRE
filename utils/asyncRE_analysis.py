# File Based Analysis Class for asynchronous Replica Exchang jobs
"""A module to analyze file-based asynchronous RE jobs
See documentation in doc/ directory.

Contributors:

Junchao Xia <junchao.xia@temple.edu>

"""

import os, re, sys, time
from configobj import ConfigObj
import random, math, numpy
import glob

def _exit(message):
    """Print and flush a message to stdout and then exit."""
    print message
    sys.stdout.flush()
    print 'exiting...'
    sys.exit(1)

class asyncRE_analysis:
    """
    Class to analyze results from asynchronous file-based RE calculations
    """

    def __init__(self, command_file, options):
        self.command_file = command_file
        self.jobname = os.path.splitext(os.path.basename(command_file))[0]
        self.keywords = ConfigObj(self.command_file)
        self._checkInput()
        self._printStatus()
        self._setupUWHAMTemplates()

    def _exit(self, message):
        _exit(message)

    def _printStatus(self):
        """Print a report of the input parameters."""
        print 'command_file =',self.command_file
        print 'jobname =',self.jobname
        for k,v in self.keywords.iteritems():
            print k,v


    def _checkInput(self):

        #Option for calculating binding free energy
        self.CalcBindEng=True
        if self.keywords.get('CALC_BIND_ENG') is None:
            self.CalcBindEng=False
        elif self.keywords.get('CALC_BIND_ENG').lower() == 'yes':
            self.CalcBindEng=True
        elif self.keywords.get('CALC_BIND_ENG').lower() == 'no':
            self.CalcBindEng=False
        else :
            self._exit("CALC_BIND_ENG option is not set right (yes or no).")

        self.BindFreeEng=True
        if self.keywords.get('BIND_FREE_ENG') is None:
            self.BindFreeEng=False
        elif self.keywords.get('BIND_FREE_ENG').lower() == 'yes':
            self.BindFreeEng=True
        elif self.keywords.get('BIND_FREE_ENG').lower() == 'no':
            self.BindFreeEng=False
        else :
            self._exit("BIND_FREE_ENG option is not set right (yes or no).")

        self.InclFlatEng=False
        if self.keywords.get('INCL_FLAT_ENG') is None:
            self.InclFlatEng=False
        elif self.keywords.get('INCL_FLAT_ENG').lower() == 'yes':
             self.InclFlatEng=True
        elif self.keywords.get('INCL_FLAT_ENG').lower() == 'no':
             self.InclFlatEng=False
        else :
             self.InclFlatEng=False
        if not self.InclFlatEng :
             print 'No flattening energy included.'


        if ( self.BindFreeEng or self.CalcBindEng) :
            if self.keywords.get('NBEGIN') is None:
                self._exit("The starting point (NBEGIN) for data needs to be specified")
            self.nbgn = int(self.keywords.get('NBEGIN'))
            if self.keywords.get('NEND') is None:
                self._exit("The end point (NEND) for data needs to be specified")
            self.nend = int(self.keywords.get('NEND'))
            if self.keywords.get('NFREQ') is None:
                self._exit("The frequency (NFREQ) for data needs to be specified")
            self.nfreq = int(self.keywords.get('NFREQ'))
        if self.keywords.get('CUMULATED') is None:
            self.cumulated=False
        elif self.keywords.get('CUMULATED').lower() == 'yes':
            self.cumulated=True
        elif self.keywords.get('CUMULATED').lower() == 'no':
            self.cumulated=False
        else :
            self._exit("CUMULATED option is not set right (yes or no).")
        if ( not self.cumulated) :
            if self.keywords.get('NDATA') is None:
                self._exit("The number of data point (NDATA) needs to be specified")
            self.ndata = int(self.keywords.get('NDATA'))
 
        # Calculate the diffision coefficent in lambda space
        if self.keywords.get('DIFF_COEFF') is None:
            self.DiffCoeff=False 
        elif self.keywords.get('DIFF_COEFF').lower() == 'yes':
            self.DiffCoeff=True
        elif self.keywords.get('DIFF_COEFF').lower() == 'no':
            self.DiffCoeff=False
        else :
            self.DiffCoeff=False

        #list of lambdas
        if self.keywords.get('LAMBDAS') is None:
            self._exit("LAMBDAS needs to be specified")
        self.lambdas = self.keywords.get('LAMBDAS').split(',')
        self.nlam = len(self.lambdas)

        #list of temperatures
        if self.keywords.get('TEMPERATURES') is None:
            self._exit("TEMPERATURES needs to be specified")
        self.temperatures = self.keywords.get('TEMPERATURES').split(',')
        self.ntemp = len(self.temperatures)
        #build parameters for the lambda/temperatures combined states
	if self.keywords.get('NREPLICAS') is None:
 	    self.nreplicas = self._buildBEDAMStates()
	else :
            self.nreplicas = int(self.keywords.get('NREPLICAS'))
        # control the replicas included for data analysis
        if self.keywords.get('REPSTART') is None:
            self.repstart = 0
        else :
            self.repstart = int(self.keywords.get('REPSTART'))
	if self.keywords.get('REPEND') is None:
            self.repend = self.repstart + self.nreplicas-1
        else :
            self.repend = int(self.keywords.get('REPEND'))

        self.ExtConf=False 
        if self.keywords.get('EXT_CONF') is None:
            self.ExtConf=False
        elif self.keywords.get('EXT_CONF').lower() == 'yes':
            self.ExtConf=True
        elif self.keywords.get('EXT_CONF').lower() == 'no':
            self.ExtConf=False
        else :
            self._exit("EXT_CONF option is not set right (yes or no).")
	if ( self.ExtConf) :
            if self.keywords.get('CONF_FORMAT').lower() == 'rst':
	       self.ConfFormat = 'rst'
            elif self.keywords.get('CONF_FORMAT').lower() == 'dms':
	       self.ConfFormat = 'dms'
            else :
               self._exit("CONF_FORMAT option is not set right (rst or dms).")
            if self.keywords.get('EXT_TEMP') is None:
               self.ExtTemp = float(300.0)
            else :
               self.ExtTemp = float(self.keywords.get('EXT_TEMP'))
            if self.keywords.get('EXT_LAMBDA') is None:
               self.ExtLambda = float(1.0)
            else :
               self.ExtLambda = float(self.keywords.get('EXT_LAMBDA'))

    def _buildBEDAMStates(self):
        self.stateparams = []
        for lambd in self.lambdas:
            for tempt in self.temperatures:
                st = {}
                st['lambda'] = lambd
                st['temperature'] = tempt
                self.stateparams.append(st)
        return len(self.stateparams)

    def _setupUWHAMTemplates(self):
        """ Setup templates for input files for R using UWHAM """

        self.uwham1D =  """

rm(list=ls())
npot.fcn <- function(x, lam) -bet*lam*x

# loads dataset
mydata = read.table("%s")
data(mydata)
lig.data <- mydata$V5
# sample size
N <- length(lig.data)
# lambda states
lam <- c(%s)
m <- length(lam)

# inverse temperature
bet <- 1.0/(0.001986209*%s)
# negative potential function


# state labels based on lambda values
# note that labels=1:m, not 0:(m-1)
state.labels <- factor(mydata$V4, labels=1:m)
# compute negative potential
neg.pot <- matrix(0, N,m)
for (j in 1:m)

neg.pot[,j] <- npot.fcn(x=lig.data, lam=lam[j])
# estimate free energies, note that size=NULL because label is given
require(UWHAM)
out <- uwham(label=state.labels, logQ=neg.pot, fisher=TRUE)
# free energies as a function of lambda, 0.36 kcal/mol is a standard
# state correction
ze <- matrix(out$ze, nrow=1, ncol=m)
-ze/bet
ve <- matrix(out$ve,nrow=1, ncol=m)
sqrt(ve)/bet

dg <- (-ze[,m]+ze[,1])/bet
dv <- sqrt(ve[,m]+ve[,1])/bet
feout <-c(dg,dv)

# print out
# printf <- function(...)print(sprintf(...))
#
write(feout,file="%s", ncolumns = 2, append = FALSE, sep = " ")

# block bootstrap for free energies, note that proc.type="serial"
# for simulated tempering data.
# To save time for package checking, this is not run.
#out.boot <- uwham.boot(proc.type="serial", block.size=10, boot.size=100, label=state.labels, logQ=neg.pot)

#-out.boot$ze/bet
#sqrt(out.boot$ve)/bet

"""

        self.uwham1Dflat =  """

rm(list=ls())

# loads dataset
mydata = read.table("%s")
data(mydata)
lig.ebind <- mydata$V5
lig.eflat <- mydata$V6

# sample size
N <- length(lig.ebind)
# lambda states
lam <- c(%s)
m <- length(lam)

# inverse temperature
bet <- 1.0/(0.001986209*%s)
# negative potential function
npot.fcn <- function(x,y,lam) {
  if (lam < 0.5) {
    pot=-bet*(lam*x-2.0*lam*y)
  } else {
    pot=-bet*(lam*x-2.0*(1-lam)*y)
  }
  return(pot)
}

# state labels based on lambda values
# note that labels=1:m, not 0:(m-1)
state.labels <- factor(mydata$V4, labels=1:m)
# compute negative potential
neg.pot <- matrix(0, N,m)
for (j in 1:m)

neg.pot[,j] <- npot.fcn(x=lig.ebind,y=lig.eflat,lam=lam[j])
# estimate free energies, note that size=NULL because label is given
require(UWHAM)
out <- uwham(label=state.labels, logQ=neg.pot, fisher=TRUE)
# free energies as a function of lambda, 0.36 kcal/mol is a standard
# state correction
ze <- matrix(out$ze, nrow=1, ncol=m)
-ze/bet
ve <- matrix(out$ve,nrow=1, ncol=m)
sqrt(ve)/bet

dg <- (-ze[,m]+ze[,1])/bet
dv <- sqrt(ve[,m]+ve[,1])/bet
feout <-c(dg,dv)

# print out
# printf <- function(...)print(sprintf(...))
#
write(feout,file="%s", ncolumns = 2, append = FALSE, sep = " ")

# block bootstrap for free energies, note that proc.type="serial"
# for simulated tempering data.
# To save time for package checking, this is not run.
#out.boot <- uwham.boot(proc.type="serial", block.size=10, boot.size=100, label=state.labels, logQ=neg.pot)

#-out.boot$ze/bet
#sqrt(out.boot$ve)/bet

"""

        self.uwham2D =  """
library('trust')
library("UWHAM")

npot.fcn <- function(e0,ebind, bet, lam) -bet*(e0 + lam*ebind)

uwham.r <- function(label,logQ,ufactormax,ufactormin=1){
  n <- dim(logQ)[1]
  m <- dim(logQ)[2]
  iniz <- array(0,dim=m)
  uf <- ufactormax
  while(uf >= ufactormin & uf >= 1){
    mask <- seq(1,n,trunc(uf))
    out <- uwham(label=label.cross[mask], logQ=neg.pot[mask,],init=iniz)
    show(uf)
    iniz <- out$ze
    uf <- uf/2
  }
  out$mask <- mask
  out
}

data.t <- read.table("%s")
data.t$e0 <- data.t$V3 - data.t$V4 * data.t$V5
lam <- c(%s)
tempt <- c(%s)
bet <- 1.0/(0.001986209*tempt)
mtempt <- length(bet)
mlam <- length(lam)
m <- mlam*mtempt
N <- length(data.t$V1)

neg.pot <- matrix(0, N,m)
sid <- 1
# note the order of (be,te)
for (be in 1:mlam) {
     for (te in 1:mtempt) {
             neg.pot[,sid] <- npot.fcn(e0=data.t$e0,ebind=data.t$V5,bet[te],lam[be])
             sid <- sid + 1
    }
}
# note levels
label.tempt <- factor(data.t$V1, levels=tempt, labels=1:mtempt)
label.lam <- factor(data.t$V4, levels=lam, labels=1:mlam)
label.cross <- (as.numeric(label.lam)-1)*mtempt + as.numeric(label.tempt)
out <- uwham.r(label=label.cross, logQ=neg.pot,ufactormax=200,ufactormin=1)
ze <- matrix(out$ze, nrow=mtempt, ncol=mlam)
-ze/bet
dg <- (-ze[,mlam]+ze[,1])/bet
# print out
# printf <- function(...)print(sprintf(...))
# print
write(dg,file="%s", ncolumns = mtempt, append = FALSE, sep = " ")

"""
    def checkBindEngData(self):
        """
check the binding free energies at different thermodynamical states.
"""
        os.system("mv lbe_temp.dat lbe_temp_old.dat")
        datafile = 'lbe_temp_old.dat'
        outfile = 'lbe_temp.dat'
        expfile = 'lbe_temp_exp.dat'
        fin = open(datafile ,"r")
        fout = open(outfile,"w")
        fexp = open(expfile,"w")
        line = fin.readline()
        while line:
             words = line.split()
             if words[3] in self.lambdas :
                fout.write(line)
             else :
                print("Warning: lambda = %s not in the defined states in the line %s" %(words[3],line))
                fexp.write(line)
             line = fin.readline()
        fin.close()
        fout.close()

    def reorgBindEngData(self):
        """
reorgnize the binding energies according to different thermodynamical states.
"""
        datafile = 'lbe_temp.dat'
        for it in range(0,self.ntemp):
          temp_str = self.temperatures[it]
          for il in range(0,self.nlam):
            lambda_str =  self.lambdas[il]
            fin = open(datafile ,"r")
            outfile = 'metadata/lbe_temp_T'+ temp_str + '_L' + lambda_str + '.dat'
	    fout = open(outfile ,"w")
	    line = fin.readline()	
	    while line:
              words = line.split()
              if words[0] == temp_str and words[3] == lambda_str:
                 fout.write(line)
              line = fin.readline()
            fin.close()
            fout.close()

    def calcBindEngData(self):
        """
calculate the averages of binding energies for different thermodynamical states.
"""
        for it in range(0,self.ntemp):
          temp_str = self.temperatures[it]
          for il in range(0,self.nlam):
            lambda_str =  self.lambdas[il]
            datafile = 'metadata/lbe_temp_T'+ temp_str + '_L' + lambda_str + '.dat'
            fin = open(datafile ,'r')
            avgfile = 'metadata/lbe_avrg_T'+ temp_str + '_L' + lambda_str + '.dat'
            fout = open(avgfile ,'a')
            data =[]
            line = fin.readline()
            while line:
              words = line.split()
              datablock=[]
              if words[0] == temp_str and words[3] == lambda_str:
                 datablock=[float(words[0])]
                 for iw in range(1,len(words)) :
                   datablock.append(float(words[iw]))
                 data.append(datablock)
              line = fin.readline()
            minvalue=numpy.min(data,axis=0)
            meanvalue=numpy.mean(data, axis=0)
            stdvalue=numpy.std(data, axis=0)
            for im in range(0,len(meanvalue)) :
	      fout.write("%s\t%s\t%s\t" %(minvalue[im],meanvalue[im],stdvalue[im]))
	    fout.write("\n")
            fin.close()
            fout.close()

    def calculateBindFreeEng(self):
        """
calculate the binding free energies at different time from the time series of binding energies.
"""
        datafile = 'lbe_temp.dat'
        deltGfile = 'DeltG.dat'
        R_inpfile = "uwham_async.R"
        lambdas_str = ' '
        for il in range(0,self.nlam-1):
            lambdas_str +=  self.lambdas[il] + ','
        lambdas_str += self.lambdas[self.nlam-1]
        temps_str = ' '
        for it in range(0,self.ntemp-1):
            temps_str +=  self.temperatures[it] + ','
        temps_str += self.temperatures[self.ntemp-1]

        if (self.ntemp == 1) :
           if self.InclFlatEng :
              uwham_input = self.uwham1Dflat % (datafile,lambdas_str,temps_str,deltGfile)
           else:
              uwham_input = self.uwham1D % (datafile,lambdas_str,temps_str,deltGfile)
        else:
            uwham_input = self.uwham2D % (datafile,lambdas_str,temps_str,deltGfile)
        f = open(R_inpfile, 'w')
        f.write(uwham_input)
        f.close()

        if self.BindFreeEng : 
           if (not self.cumulated):
              bfe_outf = open('bfe_conv_noc.dat', 'w')
           else:
              bfe_outf = open('bfe_conv.dat', 'w')
	if self.CalcBindEng :
	   os.system("mkdir metadata")
	   os.system("rm -f metadata/lbe_avrg_*.dat")

        for i in range(self.nbgn,self.nend+1):
            nhead = i*self.nfreq
            if (not self.cumulated):
                ndata = self.ndata
                ntail = self.ndata
            else:
                ndata = i*self.nfreq
                ntail = i*self.nfreq

            for ir in range(self.repstart,self.repend+1):
                inpf = "r%d/lbe.dat" %ir
                outf = "r%d/lbe_temp.dat" %ir
                lbe_cmd = 'head -n ' + str(nhead) + ' ' + inpf + '| tail -n ' + str(ntail) + ' > ' + outf
                os.system(lbe_cmd)
                if (ir == self.repstart ):
                    tmp_cmd = 'cat ' + outf + '> lbe_temp.dat'
                else:
                    tmp_cmd = 'cat ' + outf + '>> lbe_temp.dat'
                os.system(tmp_cmd)
            self.checkBindEngData()
            if self.CalcBindEng :
	       self.reorgBindEngData()
	       self.calcBindEngData() 
            if self.BindFreeEng :
               uwham_cmd = 'R CMD BATCH ' + R_inpfile + '>& uwham_async.Rout'
               os.system(uwham_cmd)
               f = open(deltGfile ,"r")
               line = f.readline()
               line = line.strip('\n')
               f.close()
               #bfedata=line.split()
               #bfe_outf.write("%d" % int(ndata))
               #for j in range(0, len(bfedata)) :
               #    bfe_outf.write("%f" % float(bfedata[j]))
               #bfe_outf.write("\n")
               if self.CalcBindEng :
                  os.system('tail -n 1 metadata/lbe_avrg_T300.0_L1.0.dat > avrg_temp.dat')                
                  f = open("avrg_temp.dat" ,"r")
                  line_avrg = f.readline()
                  line_avrg = line_avrg.strip('\n')
                  f.close()
                  line = str(nhead) + '\t' + line + '\t' + line_avrg + '\n' 
               else :
		  line = str(nhead) + '\t' + line + '\n'

               bfe_outf.write(line)
	if self.BindFreeEng :
           bfe_outf.close()

    def getStateValues(self,file):
    	if not os.path.exists(file):
           msg = 'File does not exist: %s' % file
           sys.exit(msg)
	step_line = re.compile("^ Step number:")
   	number_line = re.compile("(\s+-*\d\.\d+E[\+-]\d+\s*)+")
    	temperature_line = re.compile("^\s*input target temperature\s+(\d*\.*\d*)")
    	have_trgtemperature = 0
        have_trglambda=0
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
            	# comment out to use the instantaeous temperature 
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
                     have_trglambda=1
	    line = f.readline()
            if have_trglambda ==1 :
	       break 

    	f.close()
        stateValues=[]
        stateValues.append(data[0][1])
        nf=len(data[0])
        if self.InclFlatEng :
           stateValues.append(data[0][nf-4])
        else: 
           stateValues.append(data[0][nf-2])

	return stateValues


    def extConformers(self):
        """
extract the conformers at certain thermodynamic states.
"""
        foldername=self.ConfFormat + '_T' + str(self.ExtTemp) + '_L' + str(self.ExtLambda)
        os.system('rm -rf ' + foldername)
        makefolder_cmd = 'mkdir ' + foldername  
        os.system(makefolder_cmd)
        for ir in range(self.repstart,self.repend+1):
            cycles = []
	    out_files = glob.glob("r%d/%s_*.out" % (ir,self.jobname))
	    # print out_files
	    to_cycle = re.compile("r"+ str(ir) + "/" + self.jobname + r"_(\d+).out")
	    for f in out_files:
   		c = re.match(to_cycle, f).group(1)
     		# print c
                cycles.append(int(c))
            cycles.sort()
	    for r in cycles:
   	        #construct file name
	        datafile = "r%d/%s_%d.out" % (ir,self.jobname,r)
                #print datafil
	        stateValues=self.getStateValues(datafile)
                # print stateValues
                if self.ExtTemp == stateValues[0] and self.ExtLambda == stateValues[1] :
                   if self.ConfFormat == 'rst' :
		      conffile= "r%d/%s_%d.%s" % (ir,self.jobname,r,self.ConfFormat)
                      outfile = "%s_r%d_%d.%s" % (self.jobname,ir,r,self.ConfFormat) 
                      cp_cmd= 'cp ' + conffile + ' ' + foldername + '/' + outfile
                   elif self.ConfFormat == 'dms' :
                       infile_lig= "r%d/%s_lig_%d.%s" % (ir,self.jobname,r,self.ConfFormat)
                       outfile_lig = "%s_lig_r%d_%d.%s" % (self.jobname,ir,r,self.ConfFormat)
		       infile_rcpt= "r%d/%s_rcpt_%d.%s" % (ir,self.jobname,r,self.ConfFormat) 
                       outfile_rcpt = "%s_rcpt_r%d_%d.%s" % (self.jobname,ir,r,self.ConfFormat)
	               cp_cmd= 'cp ' + infile_lig + ' ' + foldername + '/' + outfile_lig + '; cp ' + infile_rcpt + ' ' + foldername + '/' + outfile_rcpt
	 	   os.system(cp_cmd)
		 
    def calculateLambdaDiff(self):
        """
calculate the diffision coefficient in lamda state space.
"""
        lambda_dict={}
        deltlambdas=[]
        taulambdas=[]
        histcounts=[]
        print ("make the state dictionary:")
        for il in range(0,self.nlam):
            lambda_dict[self.lambdas[il]]=il
            print ("%s : %d" %(self.lambdas[il],il))
            deltlambdas.append(0.0)
            taulambdas.append(0.0)
            histcounts.append(0)
        #print lambda_dict

        for ir in range(self.repstart,self.repend+1):
             inpf = "r%d/lbe.dat" %ir
             f=open(inpf,'r')
             lambdas_inp=[]
             line = f.readline()
             while line:
                 words = line.split()
                 lambdas_inp.append(words[3])
                 line = f.readline()                 
             f.close()
             #print ("finish reading in r%d/lbe.dat"%ir)
             lambda_pre=lambdas_inp[0]
             tau_lam=1.0
             for j in range(1,len(lambdas_inp)):
                 if lambdas_inp[j] == lambda_pre :         
                    tau_lam=tau_lam+1
                 else :
                    deltlambdas[lambda_dict[lambda_pre]] = deltlambdas[lambda_dict[lambda_pre]]+math.pow(float(lambdas_inp[j])-float(lambda_pre),2.0)
                    taulambdas[lambda_dict[lambda_pre]] = taulambdas[lambda_dict[lambda_pre]] + tau_lam
                    histcounts[lambda_dict[lambda_pre]] = histcounts[lambda_dict[lambda_pre]] + 1
                    #print ("%s %s %d" %(lambdas_inp[j], lambda_pre, lambda_dict[lambda_pre]))
                    lambda_pre = lambdas_inp[j]
                    tau_lam=1.0
             #print ("finish calculating in r%d/lbe.dat"%ir)
        f=open("diffusion_param.dat",'w')
        for il in range(0,self.nlam) :
           f.write("%d %s %15.10f %15.10f %15d \n" %(il,self.lambdas[il],deltlambdas[il],taulambdas[il],histcounts[il]))
        f.close()

        mean_deltlambda=numpy.mean(deltlambdas)/numpy.mean(histcounts)
        mean_taulambda=numpy.mean(taulambdas)/numpy.mean(histcounts)       
        diff_coeff=mean_deltlambda/(2.0*mean_taulambda)
        print ("%s avg_dl2= %15.10f avg_tau= %15.10f diff_coeff= %15.10f" % ("Diffision on lambda space:",mean_deltlambda,mean_taulambda,diff_coeff)) 


if __name__ == '__main__':

    # Parse arguments:
    usage = "%prog <ConfigFile>"

    if len(sys.argv) != 2:
        print "Please specify ONE input file"
        sys.exit(1)

    commandFile = sys.argv[1]

    print ""
    print "==============================================="
    print " Analyze Asynchronous Replica Exchange Results "
    print "==============================================="
    print ""
    print "Started at: " + str(time.asctime())
    print "Input file:", commandFile
    print ""
    sys.stdout.flush()

    async_analy = asyncRE_analysis(commandFile, options=None)
    if ( async_analy.CalcBindEng or async_analy.BindFreeEng) : 
	async_analy.calculateBindFreeEng()

    if (async_analy.ExtConf) : 
	async_analy.extConformers() 
    if (async_analy.DiffCoeff) :
        async_analy.calculateLambdaDiff()

