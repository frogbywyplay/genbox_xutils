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

from ebuild import ebuild_match, EBUILD_VAR_REGEXP
from ebuild_git import XEbuildGit, re_git_uri
from ebuild_hg import XEbuildHG, re_hg_uri
from ebuild_scm import ebuild_factory, re_tag_name
from xutils.scm import GitCmd, HGCmd

from xutils.xerror import XUtilsError

re_ov_proto = re.compile(EBUILD_VAR_REGEXP % 'XOV_(?P<ov>[a-zA-Z0-9_]+)_PROTO')
re_ov_uri = re.compile(EBUILD_VAR_REGEXP % 'XOV_(?P<ov>[a-zA-Z0-9_]+)_URI')
re_ov_version = re.compile(EBUILD_VAR_REGEXP % 'XOV_(?P<ov>[a-zA-Z0-9_]+)_REVISION')
re_ov_branch = re.compile(EBUILD_VAR_REGEXP % 'XOV_(?P<ov>[a-zA-Z0-9_]+)_BRANCH')
re_ov_portdir = re.compile(EBUILD_VAR_REGEXP % 'XOV_(?P<ov>[a-zA-Z0-9_]+)_PORTDIR')

re_ov_ebuild = re.compile(r'(\s|^)inherit.*\s(xov|target)(\s|$)')

class XEbuildTarget(XEbuildHG, XEbuildGit):
        def __init__(self, name, buffer=None):
                self.version_set = False
                self.ov_list = None
                self.gitcmd = GitCmd()
                self.hgcmd = HGCmd()
		for chunk in buffer:
			if re_git_uri.match(chunk) is not None:
				self.type = 'git'
				break
			elif re_hg_uri.match(chunk) is not None:
				self.type = 'hg'
				break
			else:
				continue
		if self.type is None:
			raise XUtilsError(error='internal error',
                                          error_log='unkonwn type for genbox config repo')
		elif self.type == 'git':
			XEbuildGit.__init__(self, name, buffer)
		else: #self.type == 'hg'
			XEbuildHG.__init__(self, name, buffer)

        def check_type(file):
                global re_ov_ebuild
                return ebuild_match(file, re_ov_ebuild.search) is not None
        check_type = staticmethod(check_type)

        def get_type(self):
                return 'target'

        def get_branch(self):
                if not self.ov_list:
                        self._get_ov_list()

                branches = []
                for ov in self.ov_list:
                        branches[ov['name']] = ov['branch']
		if self.type == 'git':
	                return (XEbuildGit.get_branch(self), branches)
		else:
	                return (XEbuildHG.get_branch(self), branches)

        def get_version(self):
                if not self.ov_list:
                        self._get_ov_list()

                vers = {}
                for ov in self.ov_list:
                        vers[ov['name']] = ov.get('hash', ov['branch'])
		if self.type == 'git':
	                return (XEbuildGit.get_branch(self), vers)
		else:
	                return (XEbuildHG.get_branch(self), vers)

        def info(self):
		if self.type == 'git':
	                res = XEbuildGit.info(self)
		else:
	                res = XEbuildHG.info(self)
                if self.ident:
                        res += "    Overlays:\n"
                        for ov in self.ident['overlays']:
                                res += "\n"
                                for val in [ 'name', 'uri', 'proto', 'hash', 'branch' ]:
                                        if ov.has_key(val):
                                                res += "        %-15s: %s\n" % (val, ov[val])
                                if ov.has_key('tags'):
                                        res += "        %-15s:" % 'tags'
                                        for tag in ov['tags']:
                                                res += ' %s' % tag
                                        res += '\n'
                return res

        def set_version(self, version, check=False, name=None, partial=False):
                """
                        @param version a version tuple ( profile_hash, ov_map )
                               ov_map is a map of overlay names and revisions
                               (ex: { 'wms' : 1234, 'sdk' : 12 }
                        @param name not used with this ebuild, always follows the rule :
                               xxx.0 -> xxx.conf_ver.ov1_ver.ov2_ver...
                        @param partial only bump overlays listed in version
                """
		user_ver = name and name[:5] == 'user:' and re_tag_name.match(name[5:])
                if self.version_set:
                        raise XUtilsError(error='internal error',
                                          error_log='version must be set only once')
                else:
                        self.version_set = True

                if type(version) == str:
                        version = ( version, {} )
                elif not version[1]:
                        version = ( version[0], {} )

		if self.type == 'git':
			if name:
		                XEbuildGit.set_version(self, version[0], check, name)
			else:
		                XEbuildGit.set_version(self, version[0], check)
		else:
			if name:
	                	XEbuildHG.set_version(self, version[0], check, name)
			else:
	                	XEbuildHG.set_version(self, version[0], check)
                self.ident['overlays'] = self._identify_ovs(version[1], partial)

                conf_num = self.pv['number'].pop(-1)
                for num_ov, ov in enumerate(self.ident['overlays']):
                        upper_name = ov['name'].upper()

                        if check and version[1].has_key(ov['name']):
                                # This overlay revision is updated, let's check it    
                                branch = self._get_ov_branch(ov['name'])
                                if branch != ov['branch']:
                                        raise XUtilsError(error='branch mismatch',
                                                          error_log="%s is on %s not %s for overlay %s" \
                                                          % (ov['hash'], ov['branch'], branch, ov['name']))

                        if partial and not ov.has_key('hash'):
                                self.pv['number'].append('0')
                                continue
                        replaced = False
                        for i, line in enumerate(self.buffer):
                                match = re_ov_version.match(line)
                                if match and replaced != i and match.group('ov') == upper_name:
                                        if 'tags' in ov:
                                            tags = ' '.join(ov['tags'])
                                        else:
                                            tags = '<xbump is unable to list tags of a remote git repository>'
                                        self.buffer[i] = "# Tags: %s\n" % tags
                                        self.buffer.insert(i + 1, "XOV_%s_REVISION=\"%s\"\n" % (upper_name, ov['hash']))
                                        replaced = True
                                        self.ov_list[num_ov].update(ov)
                                        if 'tags' in ov:
                                            self.pv['number'].append(ov['num'])
                                        else:
                                            self.pv['number'].append(ov['hash'][:7])
                                        break
                                        # Continue to search for ugly corrupted ebuilds

                        if not replaced:
                                for i, line in enumerate(self.buffer):
                                        match = re_ov_branch.match(line)
                                        if match and match.group('ov') == upper_name:
                                                self.buffer.insert(i + 1, "XOV_%s_REVISION=\"%s\"\n" % (upper_name, ov['hash']))
                                                self.buffer.insert(i + 1, "# Tags: %s\n" % ' '.join(ov['tags']))
                                                self.ov_list[ov['name']].update(ov)
                                                self.pv['number'].append(ov['num'])
                                                replaced = True
                                                break
                        if not replaced:
                                raise XUtilsError('corrupted target ebuild')
                # Use the conf shortnum for last number
                self.pv['number'].append(conf_num)
		if user_ver:
			self.pv['number'] = name[5:].split('.')
                self.pr = None

        def _get_ov_branch(self, ov_name):
                if not self.ov_list:
                        self._get_ov_list()

                for ov in self.ov_list:
                        if ov.get('name', None) == ov_name:
                                return ov.get('branch', None)
                return None

        def _get_ov_list(self):
                global re_ov_proto
                global re_ov_uri
                global re_ov_version
                global re_ov_branch
                global re_ov_portdir
                list = []
                data = {}

                if self.ov_list:
                        return self.ov_list

                self.ov_list = []
                for val, re in [
                                ( 'proto', re_ov_proto  ),
                                ( 'uri', re_ov_uri ),
                                ( 'hash', re_ov_version ),
                                ( 'branch', re_ov_branch ),
                                ( 'portdir', re_ov_portdir ),
                               ]:
                        for match in self.get_var(re, dict=True, all=True):
                                name = match['ov'].lower()
                                value = match['value']

                                if not value or len(value) == 0:
                                        continue
                                if not data.has_key(name):
                                        data[name] = {}
                                        list.append(name)
                                data[name][val] = match['value']

                for ov in list:
                        data[ov]['name'] = ov
                        if data[ov].has_key('portdir'):
                                self.ov_list.insert(0, data[ov])
                        else:
                                self.ov_list.append(data[ov])
                return self.ov_list

        def _identify_ovs(self, version_list, partial=False):
                """
                        @param version_list a list of overlays revisions
                        @param partial when set to False revisions of every overlays will be set to a hash 
                """
                ov_list = []
                for ov in self._get_ov_list():
                        ov_list.append(ov.copy())

                for ov in ov_list:
                        if version_list and ov['name'] in version_list.keys():
                                version = version_list[ov['name']]
                        elif ov.has_key('hash'):
                                version = ov['hash']
                        elif not partial:
                                version = ov['branch']
                        else:
                                version = None

                        if version:
                                if ov['proto'] == 'mercurial':
                                    ident = self.hgcmd.identify(ov['uri'], version)
                                    ov['num'] = ident['num']
                                    ov['hash'] = ident['hash']
                                    ov['tags'] = self.hgcmd.tags(ov['uri'], version)
                                elif ov['proto'] == 'git':
                                    out = self.gitcmd.ls_remote(ov['uri'], version)
				    if version in out:
				    	for ref in out.splitlines():
						if version in ref:
							ov['hash'] = ref.split()[0]
				    else:
				    	ov['hash'] = version
                                else:
                                    raise ValueError("unsupported SCM: %s" % ov)
                return ov_list

        def get_latest(self):
		if self.type == 'git':
	                return (XEbuildGit.get_latest(self), None)
		else:
                	return (XEbuildHG.get_latest(self), None) # Latest revision of overlays will be probed later

        def is_template(self):
                return self.pv['number'][-1] == "0"

        def _get_base_uri(self):
		if self.type == 'git':
	                return XEbuildGit._get_base_uri(self)
		else:
                	return XEbuildHG._get_base_uri(self)

ebuild_factory.register(XEbuildTarget)

