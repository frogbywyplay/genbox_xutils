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

from xutils import XUtilsError
from xutils.output import warn

# Parsing output of 'git ls-remote' command.
RE_LS_REMOTE = re.compile(r'^(?P<hash>[0-9a-f]{40})\t'
	'(HEAD|refs/((?P<rev>tags|heads|remotes)/)?'
		'(?P<name>\S*(\^{})?(/(master|HEAD))?))$')


def is_hash(v):
	'''Tests if the value could be a SHA1.'''
	if not isinstance(v, str):
		return False
	l = len(v)
	# 'man git-rev-parse', --short: ... The minimum length is 4.
	if l < 4 or l > 40:
		return False
	for i in v:
		if i not in "0123456789abcdef":
			return False
	return True


class Base(object):
	'''Base GIT access class.'''

	def __init__(self, uri):
		self._uri = uri

	def get_uri(self):
		return self._uri

	uri = property(get_uri, None, None, "URL of the git repository.")

	def run_cmd(self, cmd):
		env={'GIT_DIR' : self.uri, 'LC_ALL' : 'C',
			'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK','') }
		p = Popen(cmd, env=env, stdout=PIPE, stderr=PIPE)
		(stdout, stderr) = p.communicate()
		return (p.returncode, stdout, stderr)

	def get_hash(self, revision):
		'''Resolve a hash from an arbitrary revision.

		Returns None if the revision is unknown.
		See 'man gitrevisions'.'''
		if not revision.endswith('^{}'):
			return self.resolve(revision, True)
		# 'ls-remote' doesn't expand "^{}" suffixes,
		# it treats them 'as-is', let's expand...
		r = self.resolve(revision, True)
		if r:
			return r
		# miss: try again without the suffix
		r = self.resolve(revision[:-3], True)
		if r:
			# the resolution was got not from initial version but truncated
			warn("The hash %r has been resolved from %r, initial revision was %r." %
				(r, revision[:-3], revision))
		return r

	def resolve(self, revision, ret_hash):
		'''Resolve a revision from an arbitrary revision using 'ls-remote'.

		Returns None if the revision is unknown.
		See 'man gitrevisions'.'''

		# --exit-code: Exit with status "2" when no matching refs
		# are found in the remote repository.
		cmd = ['git', 'ls-remote', '--exit-code', self.uri]

		if not revision:
			raise XUtilsError(
				error="Cannot resolve empty revision: %r" % revision)

		# Frist try: the specified revision?
		(retval, out, err) = self.run_cmd(cmd + [revision, ])
		if retval == 2:
			# Second: could be a hash
			if not ret_hash and not is_hash(revision):
				return None
			# let's enumerate all revisions and check thier hashes
			(retval, out, err) = self.run_cmd(cmd)
			if retval != 0:
				raise XUtilsError(
					error="'git ls-remote' for %r failed, uri=%r" % (revision, self.uri),
					num=retval, error_log=err)
			revs = []
			for i in out.splitlines():
				if i.startswith(revision):
					if ret_hash:
						return i.split()[0]
					m = RE_LS_REMOTE.match(i)
					if not m:
						raise XUtilsError(
							error="Parsing 'git ls-remote' for %r failed, uri=%r" % (revision, self.uri),
							error_log=i)
					if m.group('rev') == 'remotes':
						continue
					n = m.group('name')
					if n:
						revs.append(n)
			return revs if revs else None
		if retval != 0:
			raise XUtilsError(
				error="'git ls-remote' for %r failed, uri=%r" % (revision, self.uri),
				num=retval, error_log=err)
		res = []
		for i in out.splitlines():
			m = RE_LS_REMOTE.match(i)
			if not m:
				raise XUtilsError(
					error="Parsing 'git ls-remote' for %r failed, uri=%r" % (revision, self.uri),
					error_log=out)
			if m.group('rev') == 'remotes':
				continue
			if res:
				raise XUtilsError(
					error="Revision %r is ambiguous, uri=%r" % (revision, self.uri),
					error_log=out)
			if ret_hash:
				res = m.group('hash')
			elif m.group('name'):
				res.append(m.group('name'))
			else:
				res.append('HEAD')
		if not res:
			raise XUtilsError(
				error="Cannot resolve %r, uri=%r" % (revision, self.uri),
				error_log=out)
		return res

	def tags(self, revision=None):
		if revision:
			return self.resolve(revision, False)
		# enumerate all
		(retval, out, err) = self.run_cmd(['git', 'ls-remote', self.uri])
		if retval != 0:
			raise XUtilsError(
				error="'git ls-remote' for %s failed" % self.uri,
				num=retval, error_log=err)
		t2h = {}
		for i in out.splitlines():
			m = RE_LS_REMOTE.match(i)
			if not m:
				raise XUtilsError(
					error="Parsing 'git ls-remote' for %r failed" % self.uri,
					error_log=i)
			if m.group('name'):
				if m.group('rev') == 'tags':
					t2h[m.group('name')] = m.group('hash')
			else:
				t2h["HEAD"] = m.group('hash')
		return t2h

	def check_revision(self, revision, branch):
		'''Minimal implementation of revision-branch check.'''
		if not self.resolve(branch, False):
			raise XUtilsError(error="Wrong branch in %r: %r" % (self.uri, branch))
		tags = self.tags()
		h = is_hash(revision)
		for i in tags:
			if i == revision:
				return True
			if h and tags[i].startswith(revision):
				warn("No check for relation between the "
					"branch %r and the revision %r in %r." %
					(branch, revision, self.uri))
				return True
		return False


class Local(Base):
	'''Local GIT access to the working tree.'''

	def __init__(self, uri, verbose=True):
		if verbose and is_remote(uri):
			raise XUtilsError(error="Not a local uri: %r" % uri)
		if uri.startswith("file:///"):
			uri = uri[7:]
		g = os.path.join(uri, '.git')
		if os.path.exists(g):
			uri = g
		Base.__init__(self, uri)

	def __git_cmd(self, cmd):
		return self.run_cmd(['git' ] + cmd)

	def get_hash(self, revision):
		'''Resolve a hash from an arbitrary revision.'''
		cmd = ['rev-parse', revision]
		(cmd_ret, out, err) = self.__git_cmd(cmd)
		if cmd_ret:
			return None
		out = out.strip()
		if is_hash(out):
			return out
		raise XUtilsError(error="Paring output of 'rev-parse' for %r failed" % revision,
			num=cmd_ret, error_log=out)

        def tag(self, version, tag, message=None):
                cmd = ['tag', '-a', tag, version]
                if message is not None:
                        cmd += ['-m', '\'%s\'' % message]
                else:
                        cmd += ['-m', '']

                (cmd_ret, out, err) = self.__git_cmd(cmd)
                if cmd_ret != 0:
			raise XUtilsError(error="'git tag' for %r failed" % version,
				num=cmd_ret, error_log=err)

        def add(self, files):
                cmd = ['add']
                if type(files) is str:
                        cmd.append(files)
                else:
                        cmd += files
                (cmd_ret, out, err) = self.__git_cmd(cmd)
                if cmd_ret != 0:
                        raise XUtilsError(
				error="'git add' for %r failed" % files,
				num=cmd_ret, error_log=err)

        def rm(self, files):
                cmd = ['rm']
                if type(files) is str:
                        cmd.append(files)
                else:
                        cmd += files
                (cmd_ret, out, err) = self.__git_cmd(cmd)
                if cmd_ret != 0:
                        raise XUtilsError(error="'git rm' for %r failed" % files,
				num=cmd_ret, error_log=err)

        def commit(self, files=None, message=None):
                cmd = ['commit']

                if message is not None:
                        cmd += ['-m', message]

                if type(files) is str:
                        cmd.append(files)
                elif files is not None:
                        cmd += files

                (cmd_ret, out, err) = self.__git_cmd(cmd)
                if cmd_ret != 0:
                        raise XUtilsError(error="'git commit' failed",
				num=cmd_ret, error_log=err)

        def merge_base(self, reva, revb):
		(cmd_ret, out, err) = self.__git_cmd(['merge-base', reva, revb])
                if cmd_ret != 0:
                        raise XUtilsError(
				error="'git merge-base' for %r and %r failed" % (reva, revb),
				num=cmd_ret, error_log=err)
                return out.strip()

        def log(self, rev=None, template=None, branch=None):
                cmd = ['log']
                
                cmd.append('--no-merges')
                
                if rev:
                        cmd.append(rev)
                if template:
                        cmd += ['--format=%s' % template]
                if branch:
                        cmd += ['--branches=%s' % branch]
                
                (cmd_ret, out, err) = self.__git_cmd(cmd)
                if cmd_ret != 0:
                        raise XUtilsError(error="'git log' failed",
				num=cmd_ret, error_log=err)
                return out

        def diff(self, rev=None, file=None):
                cmd = ['diff']

                if rev:
                        cmd.append(rev)
                if file:
                        cmd += ['--',file]
                
                (cmd_ret, out, err) = self.__git_cmd(cmd)
                if cmd_ret != 0:
                        raise XUtilsError(error="'git diff' failed",
				num=cmd_ret, error_log=err)
                return out

	def contains(self, revision):
		'''Implementation of 'git branch --contains'.'''
		if not revision:
                        raise XUtilsError(error="Wrong revision for 'contains': %r" % revision)
                (cmd_ret, out, err) = self.__git_cmd(['branch', '--contains', revision])
		if cmd_ret:
			return []
		return [i[2:] if i.startswith('* ') else i.strip() for i in out.splitlines()]

	def check_revision(self, revision, branch):
		'''Check if the revision belongs to the branch.'''
		if not self.resolve(branch, False):
			raise XUtilsError(error="Wrong branch in %r: %r" % (self.uri, branch))
		return branch in self.contains(revision)


#       FIXME/TODO rename and reimplement LATER
#        def push(self, uri, rev=None, dest=None):
#        def pull(self, uri, rev=None, src=None):
#        def update(self, uri, rev=None, clean=False):

def is_remote(uri):
	'''Is the argument a remote GIT repository (see GIT URLS in
	'man git-fetch').

	If it isn't a remote GIT repository, it must be an accessible path,
	i.e. the working tree.'''

	# Known GIT protocols
	if uri.startswith("ssh://") or uri.startswith("git://") or \
			uri.startswith("http://") or uri.startswith("https://") or \
			uri.startswith("ftp://") or uri.startswith("ftps://") or \
			uri.startswith("rsync://"):
		return True

	# An alternative scp-like syntax may also be used with the ssh protocol
	a = uri.find('@')
	if a > 0 and uri[:a].isalnum():
		return True

	# An accessible path on the host?
	if os.path.exists(uri[7:] if uri.startswith("file:///") else uri):
		return False

	raise XUtilsError(error="Wrong protocol or not accessible path: %r" % uri)


class Remote(Base):
	'''GIT access to remote repository.'''

	def __init__(self, uri, verbose=True):
		if verbose and not is_remote(uri):
			raise XUtilsError(error="Not a remote uri: %r" % uri)
		Base.__init__(self, uri)


def create_cmd(uri):
	'''Creates a command which corresponds to the specified GIT URL.'''
	return Remote(uri, False) if is_remote(uri) else Local(uri, False)
