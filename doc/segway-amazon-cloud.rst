============================================
 Running Segway in the Amazon Compute Cloud
============================================

:Author: Jay Hesselberth <firstname dot lastname at gmail dot com>
:Organization: University of Colorado School of Medicine
:Revision: $Revision: 1.2 $
:Date: $Date: 2010/08/08 00:52:30 $

Overview
========

We have implemented the **Segway** <http://noble.gs.washington.edu/proj/segway/> software framework within the 
**Amazon compute cloud** <http://aws.amazon.com/ec2/> to enable genome segmentaions of arbitrary 
size and complexity to be run within a highly scalable hardware framework.

The heavy lifting is done using the **StarCluster** software package
<http://web.mit.edu/stardev/cluster/>,
which controls the setup and configuration of a basic compute cluster able to complete
Segway runs and subsequent analyses.

Our implementation consists of a StarCluster plugin that
configures Segway-specific cluster requirements, as well as specific modifications to the StarCluster configuration
file that interact with the plugin.

The plugin and config file modifications enable:

  #. Mounting EBS volumes containing Segway installations, static data and result directories;
  #. Path and environment setup to place Segway and other required executables in the users PATH;
  #. Automatic configuration of Sun Grid Engine installation with the mem_requested consumable 

.. note::

    Before using this software you need to set up an **Amazon AWS
    account**.  See <http://aws.amazon.com/> for details.

.. warning:: 

    Please read this entire document before beginning to use Segway in the Amazon cloud.  You will be paying 
    for services rendered by Amazon when using this interface, and inapproapriate use of this method can cost you more money
    than you intend to spend!

Installation & Configuration of StarCluster
===========================================

We have found StarCluster to be an extremely useful utility for setting up
and configuring compute clusters in the Amazon cloud.  There are both
stable versions of StarCluster, as well as an experimental version that
allows, for example, spot bids to be requested and load balancing of jobs.  Please
see the StarCluster docs
<http://web.mit.edu/stardev/cluster> for details.

Basic Install
-------------

One can either obtain the stable version of StarCluster
<http://web.mit.edu/stardev/cluster/downloads.html>, or use the
developmental version enabling e.g. spot instances and load balancing,
currently at
<http://github.com/rqbanerjee/StarCluster>

The stable version of StarCluster can be installed with easy_install::

    easy_install StarCluster

Alternatively, the devleopmental version can be downloaded, unpacked and
installed with::
    
    python setup.py install

from within the unpacked source directory.  Refer to the docs and requirements of
these software packages if problems are encountered.

Basic Configuration 
-------------------

StarCluster reads configuration and plugin information from a directory in
the users $HOME named ``$HOME/.starcluster``.

Running::
    
    starcluster help

immediately following installation will prompt you to create the
``$HOME/.starcluster`` directory and a basic config file template.  In this
template, you provide your Amazon AWS user credentials that allow you to
begin using AWS services.

Modifying the StarCluster configuration file
--------------------------------------------

We provide an INI-style template with Segway-specific sections that should be
added to the basic ``$HOME/.starcluster/config`` file.  These include:

  #. Cluster sections that specify parameters appropriate for small, medium and large jobs
  #. Volume sections that specify the locations of EBS mounts containing Segway builds (required), and data and result directories (optionally).
  #. Plugin sections that load and execute Segway-specific functions for setting up and configuring the compute cluster.

There are several sections in this template::

    [cluster smallcluster]
    # gsg-keypair is defined in the default StarCluster config
    # This name must match a key pair name in your AWS account
    KEYNAME = gsg-keypair
    CLUSTER_SIZE = 2
    CLUSTER_USER = sgeadmin
    CLUSTER_SHELL = bash
    # The current base x86_64 StarCluster AMI is ami-a5c42dcc
    NODE_IMAGE_ID = ami-a5c42dcc 
    MASTER_INSTANCE_TYPE = m1.large
    NODE_INSTANCE_TYPE = m1.large

    ## Volumes to mount (defined below)
    VOLUMES = segway-data, segway-build, segway-results
    ## Plugins to execute during startup (defined below)
    PLUGINS = segway-setup

    ## Additional Cluster Templates - uncomment to use
    # [cluster mediumcluster]
    # EXTENDS=smallcluster
    # NODE_INSTANCE_TYPE = m1.xlarge
    # CLUSTER_SIZE=8

    # [cluster largecluster]
    # EXTENDS=mediumcluster
    # CLUSTER_SIZE=16

    ## Use this 1-node cluster for data upload & code testing.
    ## NOTE: 32-bit installations of segway are not available, so you 
    ## cannot run a segentation with this cluster type.  Uncomment to use
    # [cluster smallcluster32]
    # KEYNAME = gsg-keypair 
    # CLUSTER_SIZE = 1
    # CLUSTER_USER = sgeadmin
    # CLUSTER_SHELL = bash
    # The base i386 StarCluster AMI is ami-d1c42db8
    # NODE_IMAGE_ID = ami-d1c42db8
    # NODE_INSTANCE_TYPE = m1.small
    # VOLUMES = segway-data, segway-build 
    # PLUGINS = segway-setup

    # Required: SEGWAY BUILD VOLUME.  Contains executables and libraries for running
    # segway, genomedata and segtools
    [volume segway-build]
    VOLUME_ID = vol-XXXXXXXX
    MOUNT_PATH = /segway-build

    # Optional: SEGWAY DATA VOLUME
    [volume segway-data]
    VOLUME_ID = vol-YYYYYYYY
    MOUNT_PATH = /segway-data

    # Optional: SEGWAY RESULTS VOLUME
    [volume segway-results]
    VOLUME_ID = vol-ZZZZZZZZ
    MOUNT_PATH = /segway-results

    ## Segway-specific plugins 

    [plugin segway-setup]
    SETUP_CLASS = segway_plugin.Setup
    # segway_path must correspond to path setup for the SEGWAY BUILD VOLUME (above)
    segway_path = /segway-build

Paste these sections into the existing ``$HOME/.starcluster/config`` file to
use them during cluster activation.  Note that small / medium / largecluster
configs are specified in the default installation config file, so you need
to comment these out to prevent naming conflicts.

Multiple types of clusters can be configured to adapt to the needs of a
given analysis.  For example, segmentations of data collected for small
genomes (e.g. *Saccharomyces cerevisiae*) are unlikely to have
significant memory requirements during analysis, and so high CPU, low memory EC2 instance types (c1.xlarge)
can be used.  For more complicated runs, large-memory instances can be
employed (e.g.m1.xlarge and the m2.XXX series).  You should familiarize 
yourself with the types of instances available in EC2 <http://aws.amazon.com/ec2/instance-types/>
and their costs <http://aws.amazon.com/ec2/pricing/>.

In addition, if you use the developmental version of StarCluster you can run these instance types
at significantly reduced cost using spot instances <http://aws.amazon.com/ec2/spot-instances/>, which allow one
to bid for the time of a given instance.  One (possibly signficant) disadvantage of using spot instances
is that once the bid price exceeds your maximum bid, your instances will be terminated immediately, possibly during important
phases of a analysis.  Luckily, Segway is flexible enough that interrupted runs can be restarted reliably.

Installing the StarCluster plugin for Segway
--------------------------------------------

We provide a plugin for StarCluster to setup and configure
the Segway-specific portions of the cluster, including mounting EBS
volumes, setting PATH variables and modifying the SGE configuration.  The
following should be copied into a file named ``segway_plugin.py`` and
moved into the StarCluster plugins directory
(``$HOME/.starcluster/plugins``). Alternatively, you can put ``segway_plugin.py`` into your
PYTHONPATH.  The naming is important; if this is modified, the config file
should be updated in the ``plugins`` sections::

    #! /usr/bin/env python

    ''' Starcluster plugin for setting up segway requirements on a starcluster cluster instance.

    Uses specific PATH requirements in AWS snapshot snap-dbe720b4.  Users must
    make a copy of the snapshot into an EBS volumne.
    '''
    __version__ = '$Revision: 1.8 $'

    from starcluster.clustersetup import ClusterSetup
    from starcluster.logger import log

    ## versions
    SEGWAY_PKG_VER = '1.0.2'
    GENOMEDATA_PKG_VER = '1.2.2'
    SEGTOOLS_PKG_VER = '1.1.6'

    ## host files
    SGE_PROFILE = '/etc/profile.d/sge.sh'
    SEGWAY_PROFILE = '/etc/profile.d/segway.sh'
    ROOT_BASH_PROFILE = '/root/.bash_profile'
    MOTD_TAIL_FILE = '/etc/motd.tail'

    PYTHON_VERSION="2.6"
    SEGWAY_SGE_SETUP=("python %(base)s/arch/%(arch)s/lib/python%(py_version)s"
                     "/segway-%(segway_version)s-py%(py_version)s.egg/segway/cluster/sge_setup.py")
    ## Global vars

    # XXX:opt Make this an option eventually, only 64-bit available for now
    ARCH = 'Linux-x86_64'

    # optionally shutdown these services - must match services in /etc/init.d
    # XXX:opt should pass these in using config file
    SHUTDOWN_SERVICES = ['apache2','mysql']

    PROFILE_TMPL = '''
    ## Segway-specific environment
    export ARCH="%(arch)s"
    export ARCHHOME=%(base)s/arch/$ARCH # Added by install script
    export PYTHONPATH=%(base)s/arch/$ARCH/lib/python%(py_version)s:$PYTHONPATH
    export PATH=%(base)s/arch/$ARCH/bin:$PATH
    export HDF5_DIR=%(base)s/arch/$ARCH
    export C_INCLUDE_PATH=%(base)s/arch/$ARCH/include:$C_INCLUDE_PATH
    export LIBRARY_PATH=%(base)s/arch/$ARCH/lib:/segway-build/arch/$ARCH/lib64/R/lib:$LIBRARY_PATH
    export LD_LIBRARY_PATH=%(base)s/arch/$ARCH/lib:/segway-build/arch/$ARCH/lib64/R/lib:$LD_LIBRARY_PATH

    ## Profile additions
    alias ll="ls -l --color=auto"
    alias lll="ls -la --color=auto"

    cd()
    {
        builtin cd "$@"
        ls -F --color=auto
    }
    '''

    LOCAL_PROFILE_TMPL = '''
    ## Local profile additions
    export PS1=$'\\[\\033]0;\\u@\\h \\w\\007\\n\\033[32m\\]\\u@\\h \\[\\033[35m\\w\\033[0m\\]\\n> '
    '''

    MOTD_TMPL = '''
    ***************************************************************
                   === Segway %(node_type)s node ===

    segway version:         %(segway_ver)s
    genomedata version:     %(genomedata_ver)s
    segtools version:       %(segtools_ver)s

    Packages installed in %(base)s/arch/%(arch)s
    ***************************************************************
    '''

    class Setup(ClusterSetup):

        ''' Setup the environment on each node to contain the path for segway
        runs.  Shutdown services if requested '''

        def __init__(self, segway_path):

            self.segway_path = segway_path

        def run(self, nodes, master, user, user_shell, volumes):

            for node in nodes:

                nconn = node.ssh

                # base PATH to segway, genomedata, segtools executables
                base = self.segway_path

                # add segway path info to each profile of each node
                profile = nconn.remote_file(SEGWAY_PROFILE,mode='w')
                profile.write(PROFILE_TMPL % {'base':base,
                                              'arch':ARCH,
                                              'py_version':PYTHON_VERSION})
                profile.close()

                # Update local profile settings 
                local_profile = nconn.remote_file(ROOT_BASH_PROFILE,mode='w')
                local_profile.write(LOCAL_PROFILE_TMPL)
                local_profile.close()

                # Add segway-specific msg to motd
                if node.is_master():
                    node_type = 'MASTER'
                else:
                    node_type = 'COMPUTE'

                motd = nconn.remote_file(MOTD_TAIL_FILE, mode='a')
                motd.write(MOTD_TMPL % {'node_type':node_type,
                                        'segway_ver':SEGWAY_PKG_VER,
                                        'genomedata_ver':GENOMEDATA_PKG_VER,
                                        'segtools_ver':SEGTOOLS_PKG_VER,
                                        'base':base,
                                        'arch':ARCH})
                motd.close()

Launching the compute cluster
=============================

Once StarCluster has been configured, you are ready to launch a compute cluster.

.. tip::

    Because you will be paying on a per-use basis for the cluster you launch, we recommend testing
    the configuration on a small size cluster initially (i.e. cluster
    ``smallcluster``, which will setup a cluster with 1 master + 1 compute node)

To launch a small test cluster, run::

        starcluster start -c smallcluster test-cluster

where ``test-cluster`` is a ``cluster-tag`` that identifies your running
cluster.

You will see a series of messages from StarCluster indicating that your
instance(s) are coming up and the cluster is being configured, e.g.::

    $ starcluster start -c smallcluster test-cluster

    StarCluster - (http://web.mit.edu/starcluster) (v. 0.9999)
    Software Tools for Academics and Researchers (STAR)
    Please submit bug reports to starcluster@mit.edu

    >>> Validating cluster template settings...
    >>> Cluster template settings are valid
    >>> Starting cluster...
    >>> Launching a 2-node cluster...
    >>> Launching master node (AMI: ami-a5c42dcc, TYPE: m1.large)...
    >>> Creating security group @sc-test-cluster...
    >>> Launching node: node001 (AMI: ami-a5c42dcc, TYPE: m1.large)...
    ... remaining nodes launch ...
    >>> The master node is ec2-174-129-71-130.compute-1.amazonaws.com
    >>> Attaching volume vol-YYYYYYYY to master node on /dev/sdy ...
    >>> Attaching volume vol-XXXXXXXX to master node on /dev/sdx ...
    >>> Setting up the cluster...
    >>> Mounting EBS volume vol-YYYYYYYYY on /segway-build...
    >>> Mounting EBS volume vol-XXXXXXXXX on /segway-data...
    >>> Creating cluster user: sgeadmin
    >>> Configuring scratch space for user: sgeadmin
    >>> Configuring /etc/hosts on each node
    >>> Configuring NFS...
    >>> Configuring passwordless ssh for root
    >>> Configuring passwordless ssh for user: sgeadmin
    >>> Generating local RSA ssh keys for user: sgeadmin
    >>> Installing Sun Grid Engine...
    >>> Done Configuring Sun Grid Engine
    ...
    # Then, Segway specific configuration ...
    >>> Running plugin segway-env
    >>> Running plugin segway-sge
    >>> Adding SGE mem_requested consumable...
    >>> Removing head node from cluster exec queue ...
    >>> Setting SGE mem_requested for node ip-10-202-69-124.ec2.internal
    ... setup on remaining nodes ...

If you are using full price instances, this setup phase can take 5-10
minutes, depending on the size of the cluster and the instance
availability in the AWS zone.

.. note::

    You are paying for *at least* 1 hour of usage *per image* from the
    time each of the images instantiates.

.. tip::

    In addition to the StarCluster command line interface, 
    We find it helpful to use the AWS management console
    <http://aws.amazon.com/console/> as well as the ElasticFox Firefox
    extenstion
    <http://developer.amazonwebservices.com/connect/entry.jspa?externalID=609>
    to monitor and control instances and their EBS mounts.

Once can also use spot instances to reduce the cost of running the
cluster.  As long as the spot instance bid doesn't reach your maximum bid, you obtain the
instances at the bid price ($0.03 in the example below)::

    starcluster start -c smallcluter32 --bid=0.03 test-bid

.. note::

    Currently You must set ``ENABLE_EXPERIMENTAL=True`` in the StarCLuster
    config file to be able to use spot bids.

.. warning::

    If you use spot instances, we have found that cluster startup times can vary
    substantially.  If StarCluster hangs during the startup process, one
    can re-execute the ``starcluster start`` command with the
    ``--no-create`` option, which will prevent additional instances from
    being launched.  Monitor the startup of these jobs using the utilities
    in the tip below.

Logging into the cluster
========================

After launching the compute cluster, you can login to the head node and
begin running analyses::

    starcluster sshmaster <cluster-tag>

where ``<cluster-tag>`` is the cluster tag you provided to ``starcluster
start`` (e.g. ``test-cluster`` in the above example).  This will take you to the master node 
of your running compute cluster, and will report the versions and locations
of the segway installation you specified in the configuration files.

Finishing the SGE mem_requested installation
============================================

Once you login into the cluster for the first time, you must finish
initializing the SGE mem_requested consumable.  To do this, execute:

$ python /segway-build/arch/Linux-x86_64/lib/python2.6/segway-1.0.2-py2.6.egg/segway/cluster/sge_setup.py

You should see some output indicating the success or failure of this step.

XXX: need to make this automatic during cluster config, but can't seem to
get it working

Queuing segway runs and monitoring progress
===========================================

Once you are logged into the master node, you can run jobs as you normally
might on another compute cluster.  Segway and associated data are
available as you specified in StarCluster config file (e.g.
``/segway-build`` and ``/segway-data``)

Another useful monitoring tool is in the StarCluster experimental branch,
which allows load balancing.  From the local computer with StarCluster
installed, run::
    
    starcluster loadbalance <cluster-tag>

to monitor the load on the SGE queue.  Currently, new instances are not
launched and added to the queue, but the monitoring functionality can be
helpful for tuning Segway run parameters.
     
Shutting down the compute cluster
=================================

Once you are finished with a run, you should stop the running cluster to
stop paying for the service.  On the local machine, running::

    starcluster stop <cluster-tag> 

will ask you whether you want to stop the running cluster.  Answering yes
will tear down all instances in the cluster.

.. important::

    For persistent storage of the results of your analysis, you should use an EBS
    volume that is mounted separately.  We currently create ~50 Gb EBS
    volumes and mount them on running clusters for long-term storage of results 
    (e.g. ``/segway-results`` in the config file).  See the provided StarCluster
    config template for an example of how to mount EBS volues.

.. important::

    StarCluster expects EBS volumes to be formatted in a
    specific way (i.e. with at least one partition, like /dev/sda1)
    See <http://web.mit.edu/stardev/cluster/docs/volumes.html> for
    details.

Running Segway on a Larger Cluster
==================================

Because Segway runs typically consist of 100's-1000's of small jobs, you can
employ larger-size clusters to facilitate run completion in a reasonable
time.  In the provided StarCluster configuration template, we have
specified ``mediumcluster`` and ``largecluster`` configurations that can be
used for these larger jobs.

.. caution::

    Be careful when changing ``CLUSTER_SIZE``
    parameters in the config file.  You don't want to start more instances
    than the job needs.

Cost ($$$) of running Segway in the Amazon compute cloud
========================================================
In our limited experience so far, we have found that running Segway in the 
Amazon compute cloud is very cost effective.

For example, we have run several segmentations using a 12-instance cluster
containing a single master node (m1.large) and 11 compute nodes
(m1.xlarge).  Because segmentations scale with size and complexity, it is
difficult to estimate costs precisely.  A modest segmentation problem
(10-labels on 10-tracks) can be trained and decoded in ~4 hours.  If
you're using full price instances, this would amount to $32.64 (real
cost).  If you're using spot bids, then the cost would be $12.48 (assuming
a bid price of $0.26 for m1.xlarge)

It also costs money to store the output from segmentations, but this cost
is typically negligible.  We do routinely transfer the output off of AWS
to perform subsequent analyses (using e.g. segtools).

EBS snapshots of Segway builds 
=======================================

In addition to the above configuration file and plugin, we provide EBS 
snapshots containing functional Segway installations for use by others.

There is a publically available snapshot of a full segway / genomedata / segtools
installation with ID: **snap-dbe720b4**.  To use this, you'll need to copy the
snapshot to an EBS volume, and then mount the EBS volume under
/segway-build (if you're following the instructions from above).

Support
=======

I can provide support of this mode of segway use.  
If you use the segway mailing list (segway-users@uw.edu)
then I can reply to those messages.

