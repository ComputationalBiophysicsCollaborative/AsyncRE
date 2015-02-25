ASyncRE
==============

ASynchronous Replica Exchange (ASyncRE) is an extensible Python package enabling file-based larg-scale asynchronous parallel replica exchange molecular simulations on grid computing networks consisting of heterogeneous and distributed computing environments as well as on homogeneous high performance clusters, using the job transporting of SSH or BOINC distributed network. 

Replica Exchange (RE) is a popular generalized ensemble approach for the efficient sampling of conformations of molecular systems. In RE, the system is simulated at several states differing in thermodynamic environmental parameters (temperature, for example) and/or potential energy settings (biasing potentials, etc). Multiple copies (replicas) of the system are simulated at each state in such a way that, in addition to traveling in conformational space, they also travel in state space by means of periodic reassignments of states to replicas. Traditional synchronous implementations of RE are limited in terms of robustness and scaling because all of the replicas are simulated at the same time and state reassignments require stopping all of the replicas. In Asynchronous RE replicas run independently from each other, allowing simulations involving hundreds of replicas on distributed, dynamic and/or unreliable computing resources.

The basic idea of ASyncRE is to assign all replicas to either the running or the waiting lists, and allowing a subset of replicas in the waiting list to perform exchanges independently from the other replicas on the running list. In the previous version of ASyncRE (https://github.com/saga-project/asyncre-bigjob), the BigJob framework is used for launching, monitoring, and managing replicas on NSF XSEDE high performance resources. In the new release, to hide most of the complexities of resource allocation and job scheduling on a variety of architectures from large national supercomputing clusters to local departmental resources, we have implemented two different job transport systems: SSH transport for high performance cluster resources (such as those of XSEDE), and the BOINC transport for distributed computing on campus grid networks. State exchanges are performed for idle replicas via the filesystem by extracting and modifying data on the input/output files of the MD engine while other replicas continue to run. Support for arbitrary RE approaches is provided by simple user-provided adaptor modules which in general do not require source code-level modifications of legacy simulation engines. Currently, adaptor modules exist for BEDAM binding free energy calculations with IMPACT.

Web Pages
---------

ASyncRE: https://github.com/ComputationalBiophysicsCollaborative/AsyncRE

Installation
------------

ASyncRE depends on few modules which are easily installed from PiP: 

    pip install numpy
    pip install configobj
    pip install scp
    pip install paramiko

ASyncRE is currently distributed only by git:

    git clone https://github.com/ComputationalBiophysicsCollaborative/AsyncRE.git
    cd asyncre
    python setup.py install

A distribution archive can be created by issuing the command:

    python setup.py sdist

after which async_re-<version>.tar.gz will be found under dist/

Installation from the distribution archive:

    cd dist
    pip install async_re-<version>.tar.gz


Test
----

To test execute the "date" application

    python date_async_re.py command.inp

which will spawn a bunch of /bin/date replicas.

See additional sample application files under the examples/ subdirectory.

