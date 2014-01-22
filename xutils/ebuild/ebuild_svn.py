#
# Copyright (C) 2006-2014 Wyplay, All Rights Reserved.
# This file is part of xutils.
# 
# xutils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# xutils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see file COPYING.
# If not, see <http://www.gnu.org/licenses/>.
#
#

import re, os
from subprocess import Popen, PIPE

from ebuild import ebuild_match
from ebuild_scm import XEbuildSCM, ebuild_factory
from xportage import XPortage

from xutils import XUtilsError

SVN_DEFAULT_URI = "svn+ssh://svn.wyplay.int/opt/svn"

svn_base_uri = None

re_svn_ebuild = re.compile(r'(\s|^)inherit.*\ssubversion(\s|$)')
re_svn_path = re.compile(r'(\s|^)ESVN_REPO_PATH=\"(.*)\"')
re_svn_version = re.compile(r'(\s|^)ESVN_OPTIONS=(.*-r\s*([0-9]+).*|.*)')
re_svn_uri = re.compile(r'\s*ESVN_REPO_URI=\"(.*)\"')

class XEbuildSvn(XEbuildSCM):
        def __init__(self, name, buffer=None):
                self.version = None
                self.branch = None
                self.uri = None
                XEbuildSCM.__init__(self, name, buffer)

        def check_type(file):
                global re_svn_ebuild
                return ebuild_match(file, re_svn_ebuild.search) is not None
        check_type = staticmethod(check_type)

        def get_type(self):
                return 'svn'

        def info(self):
                res = XEbuildSCM.info(self)
                res += "    %-15s: %s\n" % ('barnch', self.get_branch())        
                res += "    %-15s: %s\n" % ('changeset', self.get_version())        
                return res

        def get_branch(self):
                global re_svn_path

                if self.branch:
                        return self.branch

                match = ebuild_match(self.buffer, re_svn_path.search)
                if match:
                        self.branch = match.group(2)
                        return self.branch
                else:
                        return None

        def set_version(self, version, check=False):
                global re_svn_version
                global re_svn_path
 
                if type(version) is not str:
                        version = str(version)
                if check:
                        latest = self.get_latest()
                        if latest < int(version):
                                raise XUtilsError("svn revision %s doesn't exist" % version)

                replaced = False
                for i, line in enumerate(self.buffer):
                        if re_svn_version.search(line):
                                self.buffer[i] = "ESVN_OPTIONS=\"-r %s\"\n" % version
                                self.version = version
                                # Continue to search for ugly corrupted ebuilds
                                replaced = True
                if replaced == True:
                        self.pv['number'][-1] = self.version
                        self.pr = None
                        return
                # ESVN_OPTIONS not found, adding it
                for i, line in enumerate(self.buffer):
                        if re_svn_path.match(line):
                                self.buffer.insert(i + 1, "ESVN_OPTIONS=\"-r %s\"\n" % version)
                                self.version = version
                                self.pv['number'][-1] = self.version
                                self.pr = None
                                return
                raise XUtilsError("corrupted svn ebuild")

        def get_version(self):
                global re_svn_version

                if self.version:
                        return self.version

                match = ebuild_match(self.buffer, re_svn_version.search)
                if match:
                        self.version = match.group(3)
                else:
                        self.version = 'HEAD'
                return self.version

        def get_uri(self):
                global svn_base_uri
                global re_svn_uri

                if self.uri:
                        return self.uri

                # Get uri from ebuild
                if self.buffer is not None:
                        match = ebuild_match(self.buffer, re_svn_uri.search)
                        if match:
                                self.uri = match.group(1)
                                return self.uri
                # Get uri from portage or return default
                if svn_base_uri is not None:
                        self.uri = svn_base_uri
                        return self.uri
                else:
                        portage = XPortage(os.getenv('ROOT', '/'))
                        svn_base_uri = portage.config["ESVN_BASE_URI"]
                        if svn_base_uri is None:
                                svn_base_uri = SVN_DEFAULT_URI
                        del portage
                        self.uri = svn_base_uri
                        return self.uri

        def _svn_cmd(self, uri, branch, cmd):
                command = ['/usr/bin/svn', cmd, "%s/%s" % (uri, branch)]
                p = Popen(command, env={
                                        'LC_ALL' : 'C',
                                        'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK')
                                       },
                          stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
                return (p.returncode, stdout, stderr)

        def get_latest(self):
                uri = self.get_uri()
                branch = self.get_branch()
                last_rev = None
                (cmd_ret, out, err) = self._svn_cmd(uri, branch, 'info')
                if cmd_ret != 0:
                        raise XUtilsError(error='svn command error',  error_log=err)
                match = re.match(r'.*Last Changed Rev: ([0-9]+)\n.*', out, re.MULTILINE | re.DOTALL)
                if match:
                        last_rev = int(match.group(1))
                else:
                        raise XUtilsError(error="Can't find svn revision", error_log=err)
                return last_rev

        def is_template(self):
                return self.pv['number'][-1] == "0"

ebuild_factory.register(XEbuildSvn)

