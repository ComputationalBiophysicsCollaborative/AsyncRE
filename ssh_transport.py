"""
SSH job transport for AsyncRE
"""
import os
import re
import sys
import time
import random
import paramiko
import multiprocessing as mp
import logging
import Queue
import scp

from transport import Transport # WFF - 2/18/15

class ssh_transport(Transport):
    """
    Class to launch and monitor jobs on a set of nodes via ssh (paramiko)
    """
    def __init__(self, jobname, compute_nodes, replicas): #changed on 12/1/14
        # jobname: identifies current asyncRE job
        # compute_nodes: list of names of nodes in the pool
        # nreplicas: number of replicas, 0 ... nreplicas-1
        Transport.__init__(self) #WFF - 2/18/15
        self.logger = logging.getLogger("async_re.ssh_transport") #WFF - 3/2/15

        # names of compute nodes (slots)
        self.compute_nodes = compute_nodes #changed on 12/1/14
        self.nprocs = len(self.compute_nodes)
                        
        # node status = None if idle
        # Otherwise a structure containing:
        #    replica number being executed
        #    process id
        #    process name
        #    ...
        self.node_status = [ None for k in range(self.nprocs)]

        # contains the nodeid of the node running a replica
        # None = no information about where the replica is running
        self.replica_to_job = [ None for k in replicas ]

        # implements a queue of jobs from which to draw the next job
        # to launch
        self.jobqueue = Queue.Queue()

    def _clear_resource(self, replica):
        # frees up the node running a replica identified by replica id
        job = None
        try:
            job = self.replica_to_job[replica]
        except:
            self.logger.warning("clear_resource(): unknown replica id %d",
                                replcica)

        if job == None:
            return None

        try:
            nodeid = job['nodeid']
        except:
            self.logger.warning("clear_resource(): unable to query nodeid")
            return None

        try:
            self.node_status[nodeid] = None
        except:
            self.logger.warning("clear_resource(): unknown nodeid %", nodeid)
            return None

        return nodeid

    def _availableNode(self):
        #returns a node at random among available nodes
        available = [node for node in range(self.nprocs)
                     if self.node_status[node] == None]
        if available == None or len(available) == 0:
            return None
        random.shuffle(available)
        return available[0]

    def _launchCmd(self, command, job):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(job['nodename']) 
        self.logger.info("SSH connection established to %s",job['nodename'])

        
        if job["remote_working_directory"]:
            mkdir_command = "mkdir -p %s" % job['remote_working_directory']
            stdin, stdout, stderr = ssh.exec_command(mkdir_command)
            output = stdout.read()
            error = stderr.read()
            stdin.close()
            stdout.close()
            stderr.close()
            scpt = scp.SCPClient(ssh.get_transport())
            for filename in job["exec_files"]:
                local_file = filename
                remote_file = job["remote_working_directory"] + "/"
                #self.logger.info("scp %s %s", local_file, remote_file) #can print out here to check the scp
                scpt.put(local_file, remote_file)
            for filename in job["job_input_files"]:
                local_file = job["working_directory"] + "/" + filename
                remote_file = job["remote_working_directory"] + "/" + filename
                scpt.put(local_file, remote_file)

            chmod_command = "chmod -R 777 %s" % job['remote_working_directory']
            stdin, stdout, stderr = ssh.exec_command(chmod_command)
            output = stdout.read()
            error = stderr.read()
            stdin.close()
            stdout.close()
            stderr.close()

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read()
        error = stderr.read()
        stdin.close()
        stdout.close()
        stderr.close()

        
        if job["remote_working_directory"]:
            for filename in job["job_output_files"]:
                local_file = job["working_directory"] + "/" + filename
                remote_file = job["remote_working_directory"] + "/" + filename
                try:
                    scpt.get(remote_file, local_file)
                except:
                    self.logger.info("Warning: unable to copy back file %s" % local_file)
            rmdir_command = "rm -rf %s" % job['remote_working_directory']
            stdin, stdout, stderr = ssh.exec_command(rmdir_command)
            stdin.close()
            stdout.close()
            stderr.close()

        job['output_queue'].put(output)
        job['error_queue'].put(error)

        ssh.close()

    def launchJob(self, replica, job_info):
        """
        Enqueues a job based on provided job info.
        """
        input_file = job_info["input_file"]
        output_file = job_info["output_file"]
        error_file = job_info["error_file"]
        executable = job_info["executable"]
        
        command = "%s %s > %s 2> %s " % ( executable, input_file, output_file, error_file)

        output_queue = mp.Queue()
        error_queue = mp.Queue()

        job = job_info
        job['replica'] = replica
        job['output_queue'] = output_queue
        job['error_queue'] = error_queue
        job['command'] = command
        job['process_handle'] = None

        self.replica_to_job[replica] = job

        self.jobqueue.put(replica)

        return self.jobqueue.qsize()

    #intel coprocessor setup
    def ModifyCommand(self,job, command):
        nodename = job['nodename']
        nodeN = job['nthreads']
        slotN = job['nslots']

        #add command to go to remote working directory
        cd_to_command = "cd %s ; " % job["remote_working_directory"]
        
        mic_pattern = re.compile("mic0" or "mic1")

        if re.search(mic_pattern, nodename):
            offset = slotN * (nodeN/4)  
            add_to_command = "export KMP_PLACE_THREADS=6C,4T,%dO ; " % offset
        else:
            add_to_command = "export OMP_NUM_THREADS=%d;"% nodeN
        new_command = add_to_command + cd_to_command + command
        #self.logger.info(new_command) #can print new_command here to check the command
        return new_command
    
    def ProcessJobQueue(self, mintime, maxtime):
        """
        Launches jobs waiting in the queue.
        It will scan free nodes and job queue up to maxtime.
        If the queue becomes empty, it will still block until maxtime is elapsed.
        """
        njobs_launched = 0
        usetime = 0
        nreplicas = len(self.replica_to_job)

        while usetime < maxtime:

            # find an available node
            node = self._availableNode()

            while (not self.jobqueue.empty()) and (not node == None):

                # grabs job on top of the queue
                replica = self.jobqueue.get()
                job = self.replica_to_job[replica]
               
                # assign job to available node
                job['nodeid'] = node
                job['nodename'] = self.compute_nodes[node]["node_name"]
                job['nthreads'] = int(self.compute_nodes[node]["threads_number"]) 
                job['nslots']   = int(self.compute_nodes[node]["slot_number"])    
                job['username'] = self.compute_nodes[node]["user_name"]
                # get the shell command
                command = job['command']
                #retrieve remote working directory of node
                job["remote_working_directory"] = self.compute_nodes[node]["tmp_folder"] + "/" + job["remote_replica_dir"]

                command=self.ModifyCommand(job,command)

                if job["remote_working_directory"] and job['job_input_files']:
                    for filename in job['job_input_files']:
                        local_file = job["working_directory"] + "/" + filename
                        remote_file = job["remote_working_directory"] + "/" + filename
                        #self.logger.info("%s %s", local_file, remote_file) #can print out here to verify files

                if self.compute_nodes[node]["arch"]:
                    architecture = self.compute_nodes[node]["arch"]
                else:
                    architecture = ""

                exec_directory = job["exec_directory"]
                lib_directory = exec_directory + "/lib/" + architecture
                bin_directory  = exec_directory + "/bin/" + architecture

                job["exec_files"] = []
                for filename in os.listdir(lib_directory):
                    job["exec_files"].append(lib_directory + "/" + filename)
                for filename in os.listdir(bin_directory):
                    job["exec_files"].append(bin_directory + "/" + filename)

                # launches job
                processid = mp.Process(target=self._launchCmd, args=(command, job))
                processid.start()

                job['process_handle'] = processid

                # connects node to replica
                self.replica_to_job[replica] = job
                self.node_status[node] = replica

                # updates number of jobs launched
                njobs_launched += 1
                node = self._availableNode()

            # waits mintime second and rescans job queue
            time.sleep(mintime)

            # updates set of free nodes by checking for replicas that have exited
            for repl in range(nreplicas):
                self.isDone(repl,0)

            usetime += mintime

        return njobs_launched


    def isDone(self,replica,cycle):
        """
        Checks if a replica completed a run.

        If a replica is done it clears the corresponding node.
        Note that cycle is ignored by job transport. It is assumed that it is
        the latest cycle.  it's kept for argument compatibility with
        hasCompleted() elsewhere.
        """
        job = self.replica_to_job[replica]
        if job == None:
            # if job has been removed we assume that the replica is done
            return True
        else:
            process = job['process_handle']
            if process == None:
                done = False
            else:
                done = not process.is_alive()
            if done:
                # disconnects replica from job and node
                self._clear_resource(replica)

                # attempt to remove item from queues
                try:
                    # wait 30sec, if not raise Queue.Empty exception
                    # this could also be modified to use .get(block=False)
                    # which is equivalent to timeout=0
                    self.logger.info("%s", job['output_queue'].get(timeout=30))
                    self.logger.info("%s", job['error_queue'].get(timeout=30))
                # if the queues timeout, raises a Queue.Empty Exception
                # note this is not a mp.Queue exception; it's from the Queue lib
                except Queue.Empty:
                    self.logger.warn("Error removing items from ssh process communication queues for r%s", replica)

                job['output_queue'].close()
                job['error_queue'].close()
                self.replica_to_job[replica] = None
            return done
