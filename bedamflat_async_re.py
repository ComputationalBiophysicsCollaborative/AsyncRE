import sys
import time
import math
import random
import logging
from async_re import async_re
from bedamtempt_async_re import bedamtempt_async_re_job

class bedamflat_async_re_job(bedamtempt_async_re_job):
    def _setLogger(self):
        self.logger = logging.getLogger("async_re.bedamflat_async_re")

    def _checkInput(self):
        bedamtempt_async_re_job._checkInput(self)


    def _extractLast_lambda_BindingEnergy_TotalEnergy(self,repl,cycle):
        """
        Extracts binding energy from Impact output
        """
        output_file = "r%s/%s_%d.out" % (repl,self.basename,cycle)
        datai = self._getImpactData(output_file)
        nf = len(datai[0])
        nr = len(datai)
        # [nr-1]: last record
        # [nf-2]: lambda (next to last item)
        # [nf-1]: binding energy (last item)
        #    [2]: total energy item (0 is step number and 1 is temperature)
        #
        # (lambda, binding energy,flattening energy,  total energy)
        return (datai[nr-1][nf-4],datai[nr-1][nf-3],datai[nr-1][nf-1],datai[nr-1][2])


    def _getPot(self,repl,cycle):
        (lmb, u, eflat, etot) = self._extractLast_lambda_BindingEnergy_TotalEnergy(repl,cycle)
        # removes lambda*u from etot to get e0. Note that this is the lambda from the
        # output file not the current lambda.
        if float(lmb) >= 0.5 :
           lmb_d = 2.0*(1-float(lmb))
        else: 
           lmb_d = 2.0*float(lmb)

        e0 = float(etot) - float(lmb)*float(u) + lmb_d*eflat;
        return (e0,float(u),lmb_d,eflat)

    def _getPar(self,repl):
        sid = self.status[repl]['stateid_current']
        lmb = float(self.stateparams[sid]['lambda'])
        tempt = float(self.stateparams[sid]['temperature'])
        kb = 0.0019872041
        beta = 1./(kb*tempt)
        if lmb >= 0.5 :
           lmb_d = 2.0*(1-lmb)
        else :
           lmb_d = 2.0*lmb

        return (beta,lmb,lmb_d)

    def _reduced_energy(self,par,pot):
        # par: list of parameters
        # pot: list of potentials
        # This is for temperature/binding potential beta*(U0+lambda*u)
        beta = par[0]
        lmb = par[1]
        lmb_d = par[2]
        e0 = pot[0]
        u = pot[1]
        eflat = pot[3]
        return beta*(e0 + lmb*u -lmb_d*eflat)

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

    rx = bedamflat_async_re_job(commandFile, options=None)

    rx.setupJob()

    rx.scheduleJobs()
