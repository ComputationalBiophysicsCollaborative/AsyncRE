import sys, time, random, math
from async_re import async_re
from impact_async_re import impact_job


class bedam_async_re_job(impact_job):

    def _checkInput(self):
        async_re._checkInput(self)
        #make sure BEDAM is wanted
        if self.keywords.get('RE_TYPE') != 'BEDAM':
            self._exit("RE_TYPE is not BEDAM")
        #BEDAM runs with IMPACT
        if self.keywords.get('ENGINE') != 'IMPACT':
            self._exit("ENGINE is not IMPACT")
        #input files
        # self.extfiles = self.keywords.get('ENGINE_INPUT_EXTFILES')
        # if not (self.extfiles is None):
        #    if self.extfiles != '':
        #        self.extfiles = self.extfiles.split(',')
        #list of lambdas
        if self.keywords.get('LAMBDAS') is None:
            self._exit("LAMBDAS needs to be specified")
        self.lambdas = self.keywords.get('LAMBDAS').split(',')
        self.nreplicas = len(self.lambdas)
        #simulation temperature
        if self.keywords.get('BEDAM_TEMPERATURE') is None:
            self._exit("BEDAM_TEMPERATURE is a required parameter")
        bedam_temperature = float(self.keywords.get('BEDAM_TEMPERATURE'))
        self.bedam_beta = 1./(0.0019872041*bedam_temperature)
#        #build parameters for the lambda states
#        self._buildBEDAMStates(lambdas)

#    def _buildBEDAMStates(self,lambdas):
#        self.stateparams = []
#        for lambd in lambdas:
#            st = {}
#            st['lambda'] = lambd
#            self.stateparams.append(st)
#        return len(self.stateparams)

    def _buildInpFile(self, replica):
        """
Builds input file for a BEDAM replica based on template input file
BASENAME.inp for the specified replica at lambda=lambda[stateid] for the
specified cycle.
"""
        basename = self.basename
        stateid = self.status[replica]['stateid_current']
        cycle = self.status[replica]['cycle_current']

        template = "%s.inp" % basename
        inpfile = "r%d/%s_%d.inp" % (replica, basename, cycle)
        lambd = self.lambdas[stateid]
        # read template buffer
        tfile = self._openfile(template, "r")
        tbuffer = tfile.read()
        tfile.close()
        # make modifications
        tbuffer = tbuffer.replace("@n@",str(cycle))
        tbuffer = tbuffer.replace("@nm1@",str(cycle-1))
        tbuffer = tbuffer.replace("@lambda@",lambd)
        tbuffer = tbuffer.replace("@jobname@",basename)
        tbuffer = tbuffer.replace("@replica@",str(replica))
        tbuffer = tbuffer.replace("@cycle@",str(cycle))
        # write out
        ofile = self._openfile(inpfile, "w")
        ofile.write(tbuffer)
        ofile.close()

        # update the history status file
        ofile = self._openfile("r%d/state.history" % replica, "a")
        ofile.write("%d %d %s\n" % (cycle, stateid, lambd))
        ofile.close()
        

    def _doExchange_pair(self,repl_a,repl_b):
        """
Performs exchange of lambdas for BEDAM replica exchange.        
"""
        cycle_a = self.status[repl_a]['cycle_current']
        sid_a = self.status[repl_a]['stateid_current']
        lambda_a = self.lambdas[sid_a]
        u_a = self._extractLast_BindingEnergy(repl_a,cycle_a)

        cycle_b = self.status[repl_b]['cycle_current'] 
        sid_b = self.status[repl_b]['stateid_current']
        lambda_b = self.lambdas[sid_b]
        u_b = self._extractLast_BindingEnergy(repl_b,cycle_b)

        dl = float(lambda_b) - float(lambda_a)
        du = float(u_b) - float(u_a)
        delta = -dl*du

        if self.keywords.get('VERBOSE') == "yes":
            print "Pair Info"
            print "%d %s %s" % (repl_a, lambda_a, u_a)
            print "%d %s %s" % (repl_b, lambda_b, u_b)
            print "dl = %f du = %f delta = %f" % (dl,du,delta)

        csi = random.random()
        if math.exp(-self.bedam_beta*delta) > csi:
            if self.keywords.get('VERBOSE') == "yes":
                print "Accepted %f %f" % (math.exp(-self.bedam_beta*delta),csi)
                print (self.status[repl_a]['stateid_current'], self.status[repl_b]['stateid_current'])
            self.status[repl_a]['stateid_current'] = sid_b
            self.status[repl_b]['stateid_current'] = sid_a
            if self.keywords.get('VERBOSE') == "yes":
                print (self.status[repl_a]['stateid_current'], self.status[repl_b]['stateid_current'])
        else:
            if self.keywords.get('VERBOSE') == "yes":
                print "Rejected %f %f" % (math.exp(-self.bedam_beta*delta),csi)

    def _extractLast_BindingEnergy(self,repl,cycle):
        """
Extracts binding energy from Impact output
"""
        output_file = "r%s/%s_%d.out" % (repl,self.basename,cycle)
        datai = self._getImpactData(output_file)
        nf = len(datai[0])
        nr = len(datai)
        return datai[nr-1][nf-1]

    def _getPot(self,repl,cycle):
        return float(self._extractLast_BindingEnergy(repl,cycle))

    def _getPar(self,repl):
        sid = self.status[repl]['stateid_current']
        lmb = self.lambdas[sid]
        return float(lmb)

    def _reduced_energy(self,par,pot):
        # par: list of parameters
        # pot: list of potentials
        # This is for binding potential beta*lambda*u
        return self.bedam_beta*par*pot


if __name__ == '__main__':

    # Parse arguments:
    usage = "%prog <ConfigFile>"
    
    if len(sys.argv) != 2:
        print "Please specify ONE input file"
        sys.exit(1)
    
    commandFile = sys.argv[1]

    print ""
    print "===================================="
    print "BEDAM Asynchronous Replica Exchange "
    print "===================================="
    print ""
    print "Started at: " + str(time.asctime())
    print "Input file:", commandFile
    print ""
    sys.stdout.flush()

    rx = bedam_async_re_job(commandFile, options=None)

    rx.setupJob()

    rx.scheduleJobs()
