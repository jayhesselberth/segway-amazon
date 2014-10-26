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
SEGWAY_SGE_SETUP=("/usr/bin/python %(base)s/arch/%(arch)s/lib/python%(py_version)s/"
                 "segway-%(segway_version)s-py%(py_version)s.egg/segway/cluster/sge_setup.py")
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

# setup SGE with mem_requested
# python %(base)s/arch/%(arch)s/lib/python%(py_version)s/segway-%(segway_version)s-py%(py_version)s.egg/segway/cluster/sge_setup.py
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
                                          'py_version':PYTHON_VERSION,
                                          'segway_version':SEGWAY_PKG_VER})
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

            # setup SGE using segway module
            # if node.is_master():
            #     cmd = SEGWAY_SGE_SETUP % {'base':base,
            #                               'arch':ARCH,
            #                               'py_version':PYTHON_VERSION,
            #                               'segway_version':SEGWAY_PKG_VER}

            #     pdb.set_trace()

            #     nconn.execute(cmd)
