# File Based Replica Exchange class
"""
The core module of ASyncRE: a framework to prepare and run file-based
asynchronous replica exchange calculations.

Contributors:
Emilio Gallicchio <emilio.gallicchio@gmail.com>
Junchao Xia <junchaoxia@hotmail.com>
Baofeng Zhang <baofzhang@gmail.com>
Bill Flynn <wflynny@gmail.com>

This code is adapted from:
https://github.com/saga-project/asyncre-bigjob
authored by:
Emilio Gallicchio
Brian Radak
Melissa Romanus

"""
import os
import sys
import time
import pickle
import random
import shutil
import argparse
import logging, logging.config

from configobj import ConfigObj
from async_re import async_re
from wcg_async_re import wcg_async_re_job

from gibbs_sampling import *

__version__ = '0.3.2-alpha2'

def _exit(message):
    """Print and flush a message to stdout and then exit."""
    print message
    sys.stdout.flush()
    print 'exiting...'
    sys.exit(1)

def _open(name, mode, max_attempts = 100, wait_time = 1):
    """
    Convenience function for opening files on an unstable filesystem.

    max_attempts : int
        maximum number of attempts to make at opening a file
    wait_time : int
        time (in seconds) to wait between attempts
    """
    attempts = 0
    f = None
    while f is None and attempts <= max_attempts:
        try:
            f = open(name,mode)
        except IOError:
            print ('Warning: unable to access file %s, re-trying in %d '
                   'second(s)...'%(name,wait_time))
            f = None
            attempts += 1
            time.sleep(wait_time)
    if attempts > max_attempts:
        _exit('Too many failures accessing file %s'%name)
    return f

class WCGManager(object):
    """
    Class that holds several async_re objects corresponding to a single WCG
    batch.  The idea is that we will have a single WCGManager which controls an
    async_re object for each structure.

    There will be a mgr control file which will contain a control fil
    We will add additional control lines to the control file which are ignored
    by the async_re parser and anything additional that we need to set in the
    async_re objects we can pass as "options" to async_re which is currently
    unused.
    """
    def __init__(self, control_file):
        self.control_file = control_file
        self.basename = os.path.splitext(os.path.basename(control_file))[0]
        self.keywords = ConfigObj(self.control_file)

        self._checkInput()

    def _setLogger(self):
        self.logger = logging.getLogger("async_re.wcg_manager")

    def _checkInput(self):
        self.minstruct = self.keywords.get("MINSTRUCT", None)
        self.maxstruct = self.keywords.get("MAXSTRUCT", None)
        if not (self.minstruct and self.maxstruct):
            _exit("MIN-/MAXSTRUCT not defined in .mgr file")
        self.minstruct, self.maxstruct = map(int, (self.minstruct, self.maxstruct))

        self.cntl_template_file = self.keywords.get("CNTL_TEMPLATE", None)
        if not self.cntl_template_file:
            _exit("CNTL_TEMPLATE not defined in .mgr file")
        with open(self.cntl_template_file, 'r') as fin:
            self.cntl_template = fin.read()

        self.struct_ext = self.keywords.get("STRUCT_EXT", None)
        if not self.struct_ext:
            _exit("STRUCT_EXT not defined in .mgr file")
        self.struct_ext = self.struct_ext.lower().strip('.')

        self.param_files = self.keywords.get("PARAM_FILES", None)
        if not self.param_files:
            _exit("PARAM_FILES not defined in .mgr file")
        self.param_files = self.param_files.split(',')
        if not all([os.path.exists(pf) for pf in self.param_files]):
            _exit("Some PARAM_FILES do not exist.")

        self.update_interval = self.keywords.get("UPDATE_INTERVAL", None)
        if not self.update_interval:
            _exit("UPDATE_INTERVAL not defined in .mgr file")
        self.update_interval = int(self.update_interval)

        self.exchange_interval = self.keywords.get("EXCHANGE_INTERVAL", None)
        if not self.exchange_interval:
            _exit("EXCHANGE_INTERVAL not defined in .mgr file")
        self.exchange_interval = int(self.exchange_interval)

        self.end_steps = self.keywords.get("END_STEPS", None)
        if not self.end_steps:
            _exit("END_STEPS not defined in .mgr file")
        self.end_steps = int(self.end_steps)

    def setupJobs(self):
        # get structure-dependent files
        inp_fmt = "{self.basename}_{struct:06}.inp"
        rst_fmt = "{self.basename}_{struct:06}_0.rst"
        rcp_fmt = "{self.basename}_{struct:06}_rcp.{ext}"
        lig_fmt = "{self.basename}_{struct:06}_lig.{ext}"
        fmts = (inp_fmt, rst_fmt, rcp_fmt, lig_fmt)
        self.struct_files = []
        for k in range(self.minstruct, self.maxstruct+1):
            d = dict(struct=k, ext=self.struct_ext, self=self)
            files = tuple([f.format(**d) for f in fmts])
            if all([os.path.exists(f) for f in files]):
                self.struct_files.append(files)
            else:
                _exit("Missing structure files for struct {}".format(k))

        # once have structure files, THEN create structure directories
        # symlink in structure-dependent files, then -independent files
        struct_dir_fmt = "{self.basename}_{struct:06}"
        self.struct_dirs = []
        for k, files in enumerate(self.struct_files, start=self.minstruct):
            struct_dir = struct_dir_fmt.format(struct=k, self=self)
            if os.path.isdir(struct_dir):
                _exit("Structure directory already exists: {}\n.  Delete and restart".format(struct_dir))

            os.mkdir(struct_dir)
            self.struct_dirs.append(struct_dir)

            # copy structure-dependent files
            for f in files:
                dst = os.path.join(struct_dir, f)
                shutil.copy2(f, dst)

            # symlink structure-independent files
            for pf in self.param_files:
                # TODO: fix this hack
                if pf != 'runimpact':
                    pf_dst = pf.replace(self.basename, struct_dir)
                else:
                    pf_dst = pf
                pf_dst = os.path.join(struct_dir, pf_dst)
                os.symlink(os.path.relpath(pf, struct_dir), pf_dst)

            # format and copy cntl files
            subname = "{self.basename}_{struct:06}".format(struct=k, self=self)
            cntl_contents = self.cntl_template.replace(self.basename, subname)
            cntl_dst = os.path.join(struct_dir, subname + '.cntl')
            with open(cntl_dst, 'w') as fout:
                fout.write(cntl_contents)

        # pair an async_re job manager to each structure
        curr_dir = os.getcwd()
        self.managers = []
        for struct_dir in self.struct_dirs:
            os.chdir(struct_dir)
            cntl_file = struct_dir + '.cntl'
            rx = wcg_async_re_job(cntl_file, options=None)
            rx.setupJob()
            self.managers.append({'rx': rx, 'last_step': 0, 'workdir': struct_dir})
            os.chdir(curr_dir)


    def _jobLoop(self, rx):
        rx.updateStatus()
        rx.print_status()
        rx.launchJobs()
        rx.updateStatus()
        rx.print_status()

        rx.updateStatus()
        rx.print_status()

        return rx.update_steps()

    def _jobCleanUp(self, rx):
        rx.updateStatus()
        rx.print_status()
        rx.waitJob()
        rx.cleanJob()

    def scheduleJobs(self):
        """
        The runtime loop of each wcg_async_re_job sits here instead of inside
        each object; the original way had while loops inside each object which
        would block any sort of central management scheme.

        There's also different logic here from the typical async_re_job.
        Instead of operating until a walltime limit is reached, each job will
        report the minimum number of steps acheived across all of its replicas
        at the end of each updating period.  Individual wcg_async_re_jobs will
        be popped out of the list of managed jobs once they hit a maximum number
        of steps (END_STEPS) in the .mgr file.  The while loop will end once all
        wcg_async_re_jobs have been popped.

        There is also asynchronous updating/exchanging, so that we can update
        less frequently than we exchange.
        """
        rootdir = os.getcwd()
        while len(self.managers):
            start_time = time.time()

            to_pop = []
            for k, manager in enumerate(self.managers):
                os.chdir(manager['workdir'])
                step_count = self._jobLoop(manager['rx'])
                manager['last_step'] = step_count

                if step_count > self.end_steps:
                    to_pop.append(k)
                os.chdir(rootdir)

            for k in to_pop:
                self.managers.pop(k)

            # sleeping
            spent_time = time.time() - start_time
            if self.update_interval == self.exchange_interval:
                # just sleep the remaining update time away
                if spent_time < self.update_interval:
                    time.sleep(self.update_interval - spent_time)
            else:
                # periodically sleep or do exchanges
                # sleep any initial time remaining before first exchange
                if spent_time < self.exchange_interval:
                    time.sleep(self.exchange_interval - spent_time)

                # then do remaining exchanges sleeping away any time left over
                time_remaining = self.update_interval - self.exchange_interval
                nexchanges = (time_remaining)/self.exchange_interval
                for i in range(nexchanges):
                    exchange_start = time.time()
                    for k, manager in enumerate(self.managers):
                        os.chdir(manager['workdir'])
                        manager['rx'].doExchanges()
                        os.chdir(rootdir)

                    exchange_time = time.time() - exchange_start
                    if exchange_time < self.exchange_interval:
                        time.sleep(self.exchange_interval - exchange_time)

        for manager in self.managers:
            os.chdir(manager['workdir'])
            self._jobCleanUp(manager['rx'])
            os.chdir(rootdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mgrfile')

    args = parser.parse_args()

    print ""
    print "==============================================="
    print "WCG BEDAM Asynchronous Replica Exchange Manager"
    print "==============================================="
    print ""
    print "Started at: " + str(time.asctime())
    print "Input file:", args.mgrfile
    print ""
    sys.stdout.flush()

    wm = WCGManager(args.mgrfile)
    wm.setupJobs()
    wm.scheduleJobs()
