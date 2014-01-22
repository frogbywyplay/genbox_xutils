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

from ebuild import ebuild_match, EBUILD_VAR_REGEXP, EBUILD_VAR_DEFTPL
from ebuild_scm import XEbuildSCM, ebuild_factory, re_tag_name
from xportage import XPortage

from xutils.scm import HGCmd
from xutils.xerror import XUtilsError

HG_DEFAULT_URI = "ssh://hg@sources.wyplay.int/"

hg_base_uri = None

re_hg_ebuild = re.compile(r'(\s|^)inherit.*\smercurial(\s|$)')
re_hg_branch = re.compile(EBUILD_VAR_REGEXP % 'EHG_BRANCH')
re_hg_version = re.compile(EBUILD_VAR_REGEXP % 'EHG_REVISION')
re_hg_uri = re.compile(EBUILD_VAR_REGEXP % 'EHG_REPO_URI')
re_hg_base_uri = re.compile(EBUILD_VAR_REGEXP % 'EHG_BASE_URI')

re_hg_is_uri = re.compile(r'.*://')

class XEbuildHG(XEbuildSCM):
        def __init__(self, name, buffer=None):
                self.version = None
                self.branch = None
                self.uri = None
                self.ident = None
                self.hgcmd = HGCmd()
                XEbuildSCM.__init__(self, name, buffer)

        def check_type(file):
                global re_hg_ebuild
                return ebuild_match(file, re_hg_ebuild.search) is not None
        check_type = staticmethod(check_type)

        def get_type(self):
                return 'mercurial'

        def get_branch(self):
                if self.branch:
                        return self.branch

                self.branch = self.get_var(re_hg_branch)
                return self.branch

        def info(self):
                res = XEbuildSCM.info(self)
                if self.ident:
                        res += "    %-15s: %s\n" % ('branch', self.ident['branch'])
                        res += "    %-15s: %s:%s\n" % ('changeset',
                                                     self.ident['num'],
                                                     self.ident['hash'])
                        if self.ident.get('tags') and len(self.ident['tags']):
                                res += "    %-15s: %s\n" % ('tags',
                                                            ' '.join(self.ident['tags']))
                        
                return res

        def set_version(self, version, check=False, name='shortrev'):
                global re_hg_version
                global re_hg_path
		user_ver = name[:5] == 'user:' and re_tag_name.match(name[5:])
 
                if name == 'tag':
                        if not version:
                                raise XUtilsError('Can\'t rename ebuild when no tag provided')
                        if not re_tag_name.match(version):
                                raise XUtilsError('Can\'t rename ebuild with %s' % version)

                if version is None:
                        version = XEbuildHG.get_version(self)

                self.ident = self.hgcmd.identify(XEbuildHG.get_uri(self), version)

                hash = self.ident['hash']

                if check:
                        if XEbuildHG.get_branch(self) and self.ident['branch'] != XEbuildHG.get_branch(self):
                                raise XUtilsError(error='branch mismatch', error_log='%s is on %s not %s' \
                                                  % (hash, self.ident['branch'], XEbuildHG.get_branch(self)))

                tags = self.hgcmd.tags(XEbuildHG.get_uri(self), hash)

                self.ident['tags'] = tags
                replaced = -1
                for i, line in enumerate(self.buffer):
                        if replaced != i and re_hg_version.match(line):
                                self.buffer[i] = "# Tags: %s\n" % ' '.join(tags)
                                self.buffer.insert(i + 1, EBUILD_VAR_DEFTPL % ('EHG_REVISION', hash))
                                replaced = i + 1
                                # Continue to search for ugly corrupted ebuilds

                if replaced == -1:
                        for i, line in enumerate(self.buffer):
                                if re_hg_branch.match(line):
                                        self.buffer.insert(i + 1, EBUILD_VAR_DEFTPL % ('EHG_REVISION', hash))
                                        self.buffer.insert(i + 1, "# Tags: %s\n" % ' '.join(tags))
                                        replaced = 1
                                        break
                if replaced != -1:
                        self.version = hash
                        if name == 'tag':
                                self.pv['number'] = version.split('.')
                        elif name == 'shortrev':
                                self.pv['number'][-1] = self.ident['num']
			elif user_ver:
				self.pv['number'] = name[5:].split('.')
                        else:
                                raise XUtilsError('Unsupported namming scheme %s' % name)
                        self.pr = None
                        return
                raise XUtilsError('corrupted HG ebuild')

        def get_version(self):
                global re_hg_version

                if self.version:
                        return self.version

                self.version = self.get_var(re_hg_version)
                if not self.version:
                        # branch ebuild assume version = branch HEAD
                        self.version = XEbuildHG.get_branch(self)
                        if not self.version:
                                raise XUtilsError('corrupted HG ebuild, can\'t find any version/branch information')
                return self.version

        def _get_base_uri(self):
                global hg_base_uri

                if self.buffer:
                        uri = self.get_var(re_hg_base_uri)
                        if uri:
                                return uri
                if hg_base_uri is not None:
                        return hg_base_uri
                else:
                        portage = XPortage(os.getenv('ROOT', '/'))
                        base_uri = portage.config["EHG_BASE_URI"]
                        if base_uri is None:
                                base_uri = EHG_DEFAULT_URI
                        del portage
                        return base_uri

        def get_uri(self):
                global re_hg_uri

                if self.uri:
                        return self.uri

                # Get uri from ebuild
                uri = self.get_var(re_hg_uri)
                if not uri:
                        raise XUtilsError(error='corrupted HG ebuild',
                                          error_log="Can't find EHG_REPO_URI")

                if re_hg_is_uri.match(uri):
                        self.uri = uri
                        return uri
                else:
                        self.uri = "%s/%s" % (self._get_base_uri(), uri)
                        return self.uri

        def get_latest(self):
                ident = self.hgcmd.identify(XEbuildHG.get_uri(self),
                                            XEbuildHG.get_branch(self))
                return ident['hash']

        def is_template(self):
                return self.pv['number'][-1] == "0"

ebuild_factory.register(XEbuildHG)

