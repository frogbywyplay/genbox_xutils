#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import os, re
from ebuild_scm import XEbuildSCM, ebuild_factory, re_tag_name
from ebuild import ebuild_match, EBUILD_VAR_REGEXP, EBUILD_VAR_DEFTPL

from xutils.scm import GitCmd
from xutils.xerror import XUtilsError
from xutils.output import warn
from xportage import XPortage

GIT_DEFAULT_URI = "ssh://git.wyplay.int/opt/git/"

git_base_uri = None

re_git_ebuild = re.compile(r'(\s|^)inherit.*\sgit(\s|$)')
re_git_branch = re.compile(EBUILD_VAR_REGEXP % 'EGIT_BRANCH')
re_git_version = re.compile(EBUILD_VAR_REGEXP % 'EGIT_REV|EGIT_REVISION')
re_git_uri = re.compile(EBUILD_VAR_REGEXP % 'EGIT_REPO_URI')
re_git_base_uri = re.compile(EBUILD_VAR_REGEXP % 'EGIT_BASE_URI')

re_git_is_uri = re.compile(r'.*://')

class XEbuildGit(XEbuildSCM):
        def __init__(self, name, buffer=None):
                self.version = None
                self.branch = None
                self.uri = None
                self.gitcmd = GitCmd()
                XEbuildSCM.__init__(self, name, buffer)

        def check_type(file):
                global re_git_ebuild
                return ebuild_match(file, re_git_ebuild.search) is not None
        check_type = staticmethod(check_type)

        def get_type(self):
                return 'git'

        def get_branch(self):
                if self.branch:
                        return self.branch

                self.branch = self.get_var(re_git_branch)
		# check that self.branch is not None else set a default value to master
		if self.branch is None:
			self.branch = 'master'
                return self.branch

        def info(self):
                res = XEbuildSCM.info(self)
                if self.ident:
                        res += "    %-15s: %s\n" % ('hash', self.ident['hash'])
                        if self.ident.get('tags') and len(self.ident['tags']):
                                res += "    %-15s: %s\n" % ('tags',
                                                            ' '.join(self.ident['tags']))

                return res

        def set_version(self, version, check=False, name='tag'):
		user_ver = name[:5] == 'user:' and re_tag_name.match(name[5:])
                if name != 'tag' and not user_ver:
                        raise XUtilsError("'%s' naming scheme is not supported with git" % name)
                elif not user_ver:
                        if not version:
                                raise XUtilsError('Can\'t rename ebuild when no tag provided')
                        if not re_tag_name.match(version):
                                raise XUtilsError('Can\'t rename ebuild with %s' % version)

                uri = XEbuildGit.get_uri(self)
                self.ident = {}
                self.ident['hash'] = self.gitcmd.get_hash(uri, version)
                hash = self.ident['hash']

		if self.gitcmd.is_github_repo(uri) and check:
			warn('Currently doesn\'t know how to check on a github repo => skip check.')
			check = False

                if check:
                        branch = XEbuildGit.get_branch(self)
                        if branch:
                                merge_base = self.gitcmd.merge_base(uri, branch, hash)
                                if not merge_base or not merge_base.startswith(hash):
                                        raise XUtilsError(error='branch mismatch', error_log='%s is not on %s' \
                                                  % (hash, branch))

                tags = []
                try:
                        tags = self.gitcmd.tags(uri, hash)
                except XUtilsError, e:
                        # it just means that git didn't find any tags in repository
                        pass


                self.ident['tags'] = tags
                replaced = -1
                for i, line in enumerate(self.buffer):
                        if replaced != i and re_git_version.match(line):
                                self.buffer[i] = "# Tags: %s\n" % ' '.join(tags)
                                self.buffer.insert(i + 1, EBUILD_VAR_DEFTPL % ('EGIT_REVISION', hash))
                                replaced = i + 1
                                # Continue to search for ugly corrupted ebuilds
                if replaced == -1:
                        for i, line in enumerate(self.buffer):
                                if re_git_branch.match(line):
                                        self.buffer.insert(i + 1, EBUILD_VAR_DEFTPL % ('EGIT_REVISION', hash))
                                        self.buffer.insert(i + 1, "# Tags: %s\n" % ' '.join(tags))
                                        replaced = 1
                                        break
                if replaced != -1:
                        self.version = hash
			if not user_ver:
				self.pv['number'] = version.split('.')
			else:
				self.pv['number'] = name[5:].split('.')
                        self.pr = None
                        return
                raise XUtilsError('corrupted Git ebuild')

        def get_version(self):
                global re_git_version

                if self.version:
                        return self.version

                self.version = self.get_var(re_git_version)
                if not self.version:
                        # branch ebuild assume version = branch HEAD
                        self.version = XEbuildGit.get_branch(self)
                        if not self.version:
                                raise XUtilsError('corrupted Git ebuild, can\'t find any version/branch information')
                return self.version

        def _get_base_uri(self):
                global git_base_uri

                if self.buffer:
                        uri = self.get_var(re_git_base_uri)
                        if uri:
                                return uri
                if git_base_uri is not None:
                        return git_base_uri
                else:
                        portage = XPortage(os.getenv('ROOT', '/'))
                        base_uri = portage.config["EGIT_BASE_URI"]
                        if base_uri is None:
                                base_uri = EGIT_DEFAULT_URI
                        del portage
                        return base_uri

        def get_uri(self):
                global re_git_uri

                if self.uri:
                        return self.uri

                # Get uri from ebuild
                uri = self.get_var(re_git_uri)
                if not uri:
                        raise XUtilsError(error='corrupted Git ebuild',
                                          error_log="Can't find EGIT_REPO_URI")

                if re_git_is_uri.match(uri):
                        self.uri = uri
                        return uri
                else:
		     	host = self._get_base_uri()
			self.uri = "%s/%s" % (self._get_base_uri(), uri)
                        return self.uri

        def get_latest(self):
                return self.gitcmd.get_hash(XEbuildGit.get_uri(self),
                                            XEbuildGit.get_branch(self))

        def is_template(self):
                return self.pv['number'][-1] == "0"


ebuild_factory.register(XEbuildGit)

