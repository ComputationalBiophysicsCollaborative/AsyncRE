#!/usr/bin/env python
"""
A wrapper around the core module of ASyncRE designed to manage multiple
instances of the ASyncRE framework.

Contributors:
Bill Flynn <wflynny@gmail.com>
Emilio Gallicchio <emilio.gallicchio@gmail.com>
Junchao Xia <junchaoxia@hotmail.com>
Baofeng Zhang <baofzhang@gmail.com>
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
from wcg_async_re import wcg_async_re_job
from async_re import async_re, _exit, _open

from gibbs_sampling import *

__version__ = '0.3.2-alpha2'

class WCGManager(object):
    """
    Class responsible for maintaining several (tens-hundreds) of `async_re`
    objects in a single process.  This class is designed to be operated on a
    BOINC grid with the intention of being run on IBM's WCG.  Therefore it
    eschews some of the broader functionality inherent to async_re at the
    moment.  It has not been tested using SSH-based exchanges.

    The basic idea is that each `async_re` object corresponds to a different
    "structure" of the same system.  The WCGManager expects 3 types of input
    files:

      - .mgr file     - contains all the necessary keyword arguments that
                        control how the manager operates in the exact same way
                        .cntl files control `async_re` processes.
      - structure     - for each "complex" there is a set of files which do not
        -independent    depend on the exact conformations of the "structures".
        files           These files include `agbnp2.param`, `paramstd.dat`, and
                        restraint files.   In the event that we want to
                        generalize this manager to control simulations of
                        different "systems" at once, `setupJobs` needs to be
                        modified slightly but should be doable.
      - structure     - these are all the files that vary with among
        -dependent      "structures".  Currently this list includes the `*.inp`,
        files           `*_0.rst`, `*_lig.dms`, `*_rcp.dms` files.  This list
                        can be expanded as needed but a certain format of
                        `{basename}_XXXXXX*` is expected.  For N "structures",
                        the manager expects to find 4*N "structure"-dependent
                        files in increasing numeric order from MINSTRUCT -
                        MAXSTRUCT specified in the .mgr file.

    There are three main changes that differentiate the way this runs from
    normal Async_RE.

      1 To reduce filesystem overhead, I brought back symlinking in place of
        file copying everywhere.  If this is to be run on IBM's grid, copying
        more files than is absolutely necessary could lead to significant
        overheads that we wouldn't notice on our smaller grids.  One of the
        major consequences to this was `stage_file` not working with symlinks,
        so `boinc_transport` was slightly modified in how it stages files.

      2 The main loop of each `async_re` object are not used and a new main loop
        functionality was implemented in the WCGManager class.  The `async_re`
        main loops are blocking and would not allow more than one to run at once
        unless we subprocessed them.  Instead, we loop over each `async_re`
        object and invoke a series of `updateStatus`, `print_status`, and
        `launchJobs` commands for each object.  This is what I called the
        "update step" and its frequency is controlled by `UPDATE_INTERVAL` in
        the `.mgr` file.  After the update step, each `async_re` object
        undergoes (multiple) exchange steps.  The `EXCHANGE_INTERVAL` specified
        in the `.mgr` file controls how often to exchange, and if signficantly
        smaller than the `UPDATE_INTERVAL`, all `async_re` objects can exchange
        many times per update step.  Everything sleeps in the time between when
        the update step finishes and the first exchange attempts are made, and
        between exchange attempts (assuming there are few enough `async_re`
        objects given the specified update/exchange intervals that there is time
        left over).

      3 The main loop terminates in a significantly different way as well.
        Instead of breaking once a specified walltime limit is reached, the main
        loop exits once every replica of every `async_re` object has surpassed a
        certain number of steps (specified with `END_STEPS` in the `.mgr` file).
        The works by having each `async_re` object check its replicas' steps (by
        parsing their latest output files), take the minimum, and comparing that
        to `END_STEPS`.  `async_re` objects which have surpassed the step count
        are removed from the set of objects managed by the WCGManager, and once
        that set is empty, the main loop terminates.

    For an example, see `examples/wcg_1d` and run with

        python path/to/wcg_manager.py test_system.mgr

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
