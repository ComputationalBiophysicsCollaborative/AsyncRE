import os
import re
import random
import math
import logging
from async_re import async_re

class impact_job(async_re):

    def _setLogger(self):
        self.logger = logging.getLogger("async_re.impact_async_re")

    def _launchReplica(self,replica,cycle): 
        """
        Launches a Impact sub-job
        """
        input_file = "%s_%d.inp" % (self.basename, cycle)
        log_file = "%s_%d.log" % (self.basename, cycle)
        err_file = "%s_%d.err" % (self.basename, cycle)
        
        
        if self.transport_mechanism != "SSH":
            executable = os.getcwd() + "/runimpact"
            working_directory = os.getcwd() + "/r" + str(replica)
            job_info = {"executable": executable,
                        "input_file": input_file,
                        "output_file": log_file,
                        "error_file": err_file,
                        "working_directory": working_directory,
                        "cycle": cycle}
            #delete failed file if present
            failed_file = "r%s/%s_%d.failed" % (str(replica),self.basename,cycle)
            if os.path.exists(failed_file):
                os.remove(failed_file)
        
        else:
            rstfile_p = "%s_%d.rst" % (self.basename,cycle-1)
            local_working_directory = os.getcwd() + "/r" + str(replica)
            remote_replica_dir = "%s_r%d_c%d" % (self.basename, replica, cycle)
            executable = "./runimpact"

            job_info = {
                "executable": executable,
                "input_file": input_file,
                "output_file": log_file,
                "error_file": err_file,
                "working_directory": local_working_directory,
                "remote_replica_dir": remote_replica_dir,
                "job_input_files": None,
                "job_output_files": None,
                "exec_directory": None}

            # detect which kind of architecture the node use, then choosing
            # different library files and binary files in different lib and bin
            # folders
            if self.keywords.get('EXEC_DIRECTORY'):
                exec_directory = self.keywords.get('EXEC_DIRECTORY')
            else:
                exec_directory = os.getcwd()

            job_info["exec_directory"]=exec_directory

            job_input_files = []
            job_input_files.append(input_file)
            if rstfile_p:
                job_input_files.append(rstfile_p)
            for filename in self.extfiles:
                job_input_files.append(filename)

            job_output_files = []
            job_output_files.append(log_file)
            job_output_files.append(err_file)
            output_file = "%s_%d.out" % (self.basename, cycle)
            rstfile = "%s_%d.rst" % (self.basename, cycle)

            if self.keywords.get('RE_TYPE') == 'TEMPT':
                dmsfile = "%s_%d.dms" % (self.basename, cycle)
            elif self.keywords.get('RE_TYPE') == 'BEDAMTEMPT':
                rcptfile="%s_rcpt_%d.dms" % (self.basename,cycle)
                ligfile="%s_lig_%d.dms" % (self.basename,cycle)    
            job_output_files.append(output_file)
            job_output_files.append(rstfile)
            if self.keywords.get('RE_TYPE') == 'TEMPT':
                job_output_files.append(dmsfile)
            elif self.keywords.get('RE_TYPE') == 'BEDAMTEMPT':
                job_output_files.append(rcptfile)
                job_output_files.append(ligfile)

            job_info["job_input_files"] = job_input_files;
            job_info["job_output_files"] = job_output_files;

        if self.keywords.get('VERBOSE') == "yes":
            msg = "_launchReplica(): Launching %s %s in directory %s cycle %d"
            if self.transport_mechanism is not 'SSH':
                self.logger.info(msg, executable, input_file, working_directory, cycle)
            else:
                self.logger.info(msg, executable, input_file, local_working_directory, cycle)

        status = self.transport.launchJob(replica, job_info)

        return status

    def _getImpactData(self, file):
        """
        Reads all of the Impact simulation data values temperature, energies,
        etc.  at each time step and puts into a big table
        """
        if not os.path.exists(file):
            msg = 'File does not exist: %s' % file
            self._exit(msg)
        step_line = re.compile("^ Step number:")
        number_line = re.compile("(\s+-*\d\.\d+E[\+-]\d+\s*)+")
        nsamples = 0
        data = []
        f = self._openfile(file ,"r")
        line = f.readline()
        while line:
            # fast forward until we get to the line:
            # "Step number: ... "
            while line and not re.match(step_line, line):
                line = f.readline()
            # read the step number
            if re.match(step_line, line):
                words = line.split()
                step = words[2]
                #now read up to 3 lines of numbers
                datablock = [int(step)]
                ln = 0
                while ln < 3:
                    line = f.readline()
                    if not line:
                        msg = "Unexpected end of file"
                        self._exit(msg)
                    if re.match(number_line, line):
                        for word in line.split():
                            datablock.append(float(word))
                        ln += 1
                data.append(datablock)
            line = f.readline()
        f.close()
        return data

    def _hasCompleted(self,replica,cycle):
        """
        Returns true if an IMPACT replica has successfully completed a cycle.
        """
        rstfile = "r%d/%s_%d.rst" % (replica, self.basename,cycle)
        rstfile_p = "r%d/%s_%d.rst" % (replica, self.basename,cycle-1)
        output_file = "r%s/%s_%d.out" % (replica,self.basename,cycle)
        failed_file = "r%s/%s_%d.failed" % (replica,self.basename,cycle)

        if os.path.exists(failed_file):
            return False

        try:
            #check existence of rst file
            if not os.path.exists(rstfile):
                if self.verbose:
                    self.logger.warning("Cannot find file %s", rstfile)
                return False
        except:
            self.logger.error("Error accessing file %s", rstfile)
            return False

        try:
            #check that rst file is of the correct size
            if cycle > 1:
                rstsize = os.path.getsize(rstfile)
                rstsize_p = os.path.getsize(rstfile_p)
                if not rstsize == rstsize_p:
                    if self.verbose:
                        self.logger.warning("Files %s and %s have different sizes", rstfile, rstfile_p)
                    return False
        except:
            self.logger.error("Error accessing file %s", rstfile)
            return False

        try:
            #check that we can read data from .out
            datai = self._getImpactData(output_file)
            nf = len(datai[0])
            nr = len(datai)
        except:
            if self.verbose:
                self.logger.warning("Unable to read/parse file %s", output_file)
            return False

        return True

    def _computeSwapMatrix(self, replicas, states):
        """
        Compute matrix of dimension-less energies: each column is a replica
        and each row is a state so U[i][j] is the energy of replica j in state
        i.

        Note that the matrix is sized to include all of the replicas and states
        but the energies of replicas not in waiting state, or those of waiting
        replicas for states not belonging to waiting replicas list are
        undefined.
        """
        # U will be sparse matrix, but is convenient bc the indices of the
        # rows and columns will always be the same.
        U = [[ 0. for j in range(self.nreplicas)]
             for i in range(self.nreplicas)]

        n = len(replicas)

        #collect replica parameters and potentials
        par = []
        pot = []
        for k in replicas:
            v = self._getPot(k,self.status[k]['cycle_current'])
            l = self._getPar(k)
            par.append(l)
            pot.append(v)
        if self.verbose:
            self.logger.info("Swap matrix info:")
            self.logger.info("%s", ' '.join(map(str, pot)))
            self.logger.info("%s", ' '.join(map(str, par)))

        for i in range(n):
            repl_i = replicas[i]
            for j in range(n):
                sid_j = states[j]
                # energy of replica i in state j
                U[sid_j][repl_i] = self._reduced_energy(par[j],pot[i])
        return U
