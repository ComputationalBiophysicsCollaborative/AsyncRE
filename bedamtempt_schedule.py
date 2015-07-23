"""
Simple module for lambda scheduling.  Reworked it to be as general
as possible, so it accepts exchanging, multiple temperatures, 
different job transport mechanisms.  Inherits most functionality
from bedamtempt_async_re_job (although not _checkInput).

Changes needed to the jobname.cntl file:

-   New/modified keywords
    -   LAMBDAS:  indicates the starting lambdas of all replicas
        (str)     used to specify how many replicas you want running
                  ex: "1.0,1.0,1.0,1.0,1.0" for 5 replicas
    -   LAMBDA_SCHED:  comma separated list of lambda values that
        (str)          constitute the schedule.  note that the
                       scheduler will restart the schedule when it's
                       exhausted, so make sure the end-points are
                       consistent
    -   SCHED_INTERVAL:  integer representing number of cycles before
        (int)            changing lambda values.
                  
-   Will create LAMBDAS * TEMPERATURES states.  Therefore, make sure
    LAMBDAS represents only the starting lambdas of however many
    replicas you want to run.

-   Scheduling is based purely on cycles:
    lambd_idx = ((cycle-1) / self.sched_interval) % len(self.lambda_sched)
    lambd = self.lambda_sched[lambd_idx]

Author: Bill Flynn (wflynny@gmail.com)
Date: 2015/07/23
"""

import sys
import time
import math
import random
import logging
from async_re import async_re
from bedamtempt_async_re import bedamtempt_async_re_job

class bedamtempt_schedule_job(bedamtempt_async_re_job):
    def _setLogger(self):
        self.logger = logging.getLogger("async_re.bedamtempt_schedule")

    def _checkInput(self):
        async_re._checkInput(self)

        #make sure BEDAM + TEMPERATURE is wanted
        if self.keywords.get('RE_TYPE') != 'BEDAMTEMPT':
            self._exit("RE_TYPE is not BEDAMTEMPT")
        #BEDAM runs with IMPACT
        if self.keywords.get('ENGINE') != 'IMPACT':
            self._exit("ENGINE is not IMPACT")

        #input files
        self.extfiles = self.keywords.get('ENGINE_INPUT_EXTFILES')
        if not (self.extfiles is None):
            if self.extfiles != '':
                self.extfiles = self.extfiles.split(',')

        #list of temperatures
        if self.keywords.get('TEMPERATURES') is None:
            self._exit("TEMPERATURES needs to be specified")
        temperatures = self.keywords.get('TEMPERATURES').split(',')

        #list of STARTING lambdas
        if self.keywords.get('LAMBDAS') is None:
            self._exit("LAMBDAS needs to be specified")
        st_lambdas = self.keywords.get('LAMBDAS').split(',')
        if all([lambd != st_lambdas[0] for lambd in st_lambdas]):
            self.logger.warn("Not all starting lambdas are equal!")

        #lambda schedule
        if self.keywords.get('LAMBDA_SCHED') is None:
            self._exit("LAMBDA_SCHED needs to be specified")
        self.lambda_sched = self.keywords.get('LAMBDA_SCHED').split(',')

        #build parameters for the lambda/temperatures combined states
        self.nreplicas = self._buildBEDAMStates(st_lambdas, temperatures)

        #executive file's directory
        if self.keywords.get('JOB_TRANSPORT') is 'SSH':
            if self.keywords.get('EXEC_DIRECTORY') is None:
                self._exit("EXEC DIRECTORY needs to be specified")

        #schedule interval
        if self.keywords.get('SCHED_INTERVAL') is None:
            self._exit("SCHED_INTERVAL is a required parameter!")
        self.sched_interval = int(self.keywords.get('SCHED_INTERVAL'))
        if self.sched_interval < 1:
            self._exit("SCHED_INTERVAL must be > 0!")

    def _buildBEDAMStates(self, st_lambdas, temperatures):
        self.stateparams = []
        for lambd in st_lambdas:
            for tempt in temperatures:
                st = {}
                st['lambda'] = lambd
                st['temperature'] = tempt
                self.stateparams.append(st)
        return len(self.stateparams)

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

        #remember that cycle numbering starts at 1
        lambd_idx = ((cycle-1) / self.sched_interval) % len(self.lambda_sched)
        lambd = self.lambda_sched[lambd_idx]
        self.stateparams[stateid]['lambda'] = lambd
        temperature = self.stateparams[stateid]['temperature']

        # read template buffer
        tfile = self._openfile(template, "r")
        tbuffer = tfile.read()
        tfile.close()
        # make modifications
        tbuffer = tbuffer.replace("@n@",str(cycle))
        tbuffer = tbuffer.replace("@nm1@",str(cycle-1))
        tbuffer = tbuffer.replace("@lambda@",lambd)
        tbuffer = tbuffer.replace("@temperature@",temperature)
        # write out
        ofile = self._openfile(inpfile, "w")
        ofile.write(tbuffer)
        ofile.close()

        # update the history status file
        ofile = self._openfile("r%d/state.history" % replica, "a")
        ofile.write("%d %d %s %s\n" % (cycle, stateid, lambd, temperature))
        ofile.close()

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

    rx = bedamtempt_schedule_job(commandFile, options=None)

    rx.setupJob()

    rx.scheduleJobs()
