#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import re, os, commands

from ebuild import ebuild_match, EBUILD_VAR_REGEXP
from ebuild_hg import XEbuildHG
from ebuild_scm import ebuild_factory, re_tag_name

from xutils.xerror import XUtilsError

re_hg_mq_ebuild = re.compile(r'(\s|^)inherit.*\smercurial-mq(\s|$)')
re_hg_mq_branch = re.compile(EBUILD_VAR_REGEXP % 'EHG_MQ_BRANCH')
re_hg_mq_version = re.compile(EBUILD_VAR_REGEXP % 'EHG_MQ_REVISION')

class XEbuildHG_MQ(XEbuildHG):

        def __init__(self, name, buffer=None):
                self.branch_mq = None
                self.version_mq = None
                XEbuildHG.__init__(self, name, buffer)

        def get_type(self):
                return 'mercurial-mq'

        def check_type(file):
                global re_hg_mq_ebuild
                return ebuild_match(file, re_hg_mq_ebuild.search) is not None
        check_type = staticmethod(check_type)

        def info(self):
                res = XEbuildHG.info(self)
                if self.ident:
                        res += "    %-15s: %s:%s\n" % ('MQ changeset',
                                                     self.ident['mq']['num'],
                                                     self.ident['mq']['hash'])
                        res += "    %-15s: %s\n" % ('MQ branch', self.ident['mq']['branch'])
                        if self.ident['mq'].has_key('tags'):
                                res += "    %-15s: %s\n" % ('MQ tags',
                                                            " ".join(self.ident['mq']['tags']))
                return res

        def _get_uri_mq(self):
                uri = XEbuildHG.get_uri(self)
                return uri + "/.hg/patches" 

        def _get_version_mq(self):
                global re_hg_mq_version

                if self.version_mq:
                        return self.version_mq

                self.version_mq = self.get_var(re_hg_mq_version)

                if not self.version_mq:
                        # branch ebuild assume version = branch HEAD
                        self.version_mq = self.get_branch()[1]
                return self.version_mq

        def get_branch(self):
                global re_hg_mq_branch

                if self.branch_mq:
                        return (XEbuildHG.get_branch(self), self.branch_mq)

                self.branch_mq = self.get_var(re_hg_mq_branch)
                return (XEbuildHG.get_branch(self), self.branch_mq)

        def get_version(self):
                version = XEbuildHG.get_version(self)
                return (version, self._get_version_mq())

        def set_version(self, version, check=False, name='shortrev'):
                global re_hg_mq_version
                global re_hg_mq_path
		user_ver = name[:5] == 'user:' and re_tag_name.match(name[5:])

                if name != 'shortrev' and not user_ver:
                        raise XUtilsError("'%s' naming scheme is not supported with mercurial-mq" % name)

                if type(version) == str:
                        version = ( version, self.get_branch()[1] ) 

                XEbuildHG.set_version(self, version[0], check, name)
                self.ident['mq'] = self.hgcmd.identify(self._get_uri_mq(), version[1])
                version_hash = self.ident['mq']['hash']

                if check:
                        if not self.branch_mq:
                                XEbuildHG_MQ.get_branch(self)
                        if self.branch_mq != self.ident['mq']['branch']:
                                raise XUtilsError(error='branch mismatch', error_log="%s is on %s not %s" \
                                                  % (version_hash, self.ident['mq']['branch'], self.branch_mq))

                tags = self.hgcmd.tags(self._get_uri_mq(), version_hash)
                self.ident['mq']['tags'] = tags
                replaced = -1
                for i, line in enumerate(self.buffer):
                        if replaced != i and re_hg_mq_version.search(line):
                                self.buffer[i] = "# Tags: %s\n" % ' '.join(tags)
                                self.buffer.insert(i + 1, "EHG_MQ_REVISION=\"%s\"\n" % version_hash)
                                replaced = i + 1
                                # Continue to search for ugly corrupted ebuilds
                if replaced != -1:
                        self.version_mq = version_hash
			if not user_ver:
				self.pv['suffix'] = "_p%s" % self.ident['mq']['num']
                        self.pr = None
                        return
                # EHG_MQ_REVISION not found, adding it
                for i, line in enumerate(self.buffer):
                        if re_hg_mq_branch.match(line):
                                self.buffer.insert(i + 1, "EHG_MQ_REVISION=\"%s\"\n" % version_hash)
                                self.buffer.insert(i + 1, "# Tags: %s\n" % ' '.join(tags))
                                self.version_mq = version_hash
				if not user_ver:
					self.pv['suffix'] = "_p%s" % self.ident['mq']['num']
                                self.pr = None
                                return
                raise XUtilsError('corrupted HG-MQ ebuild')

        def get_uri(self):
                return (XEbuildHG.get_uri(self), self._get_uri_mq())

        def get_latest(self):
                branches = self.get_branch()
                ident = self.hgcmd.identify(XEbuildHG.get_uri(self), branches[0])
                ident_mq = self.hgcmd.identify(self._get_uri_mq(), branches[1])

                return (ident['hash'], ident_mq['hash'])

        def is_template(self):
                return (self.pv['number'][-1] == "0") and \
                       (
                        (self.pv['suffix'] == '_p0') or \
                        (self.pv['suffix'] == '')
                       )

ebuild_factory.register(XEbuildHG_MQ)

