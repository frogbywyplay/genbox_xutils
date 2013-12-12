#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import re, os

from subprocess import Popen, PIPE

from xutils import XUtilsError
from xutils.output import warn

re_ref_tag_split = re.compile(r'^(?P<hash>\S+)\s+refs/tags/(?P<tag>\S*)(\^{})?$')

class GitCmd(object):
        __uri_split = re.compile(r'(?:.*://)?([^/]*)/(.*)')

        def __git_ssh_cmd(self, host, path, cmd):
                command = ['/usr/bin/ssh', host, 'GIT_DIR=' + path, 'git', ] + cmd
                p = Popen(command, env={
                                        'LC_ALL' : 'C',
                                        'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK','')
                                       },
                          stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
                return (p.returncode, stdout, stderr)

        def __git_file_cmd(self, uri, cmd):
                command = ['git' ] + cmd

                if os.path.exists(uri + '/.git'):
                        uri += '/.git'
                
                p = Popen(command, env={
                                        'GIT_DIR' : uri,
                                        'LC_ALL' : 'C',
                                        'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK','')
                                       },
                          stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
                return (p.returncode, stdout, stderr)

        def __git_cmd(self, uri, cmd):
                if uri.startswith('ssh://') or uri.startswith('git@'):
                        (url, path) = GitCmd.__uri_split.match(uri).groups()
			url = url[:-1] if url.endswith(':') else url
                        if path[0] != '~':
                                path = '/' + path
                        return self.__git_ssh_cmd(host=url, path=path, cmd=cmd)
                elif uri.startswith('git://'):
                        raise XUtilsError(error='git proto not supported in GitCmd (git://)')
                else:
                        return self.__git_file_cmd(uri=uri, cmd=cmd)

	def __run_cmd(self, cmd):
                p = Popen(cmd, env={
                                        'LC_ALL' : 'C',
                                        'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK','')
                                       },
                          stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
                return (p.returncode, stdout, stderr)

	def is_github_repo(self, uri):
		""" Return a boolean to validate whether uri refers to a github repository or not."""
		# This method is required because github.com forbids ssh commands
		cmd = ['git', 'config', '--get', 'remote.origin.url']
		(ret, out, err) = self.__run_cmd(cmd)
		remote_uri = out if ret == 0 else uri
		return True if 'github.com' or 'gitlab' in remote_uri else False

        def get_hash(self, uri, version):
                """ return a hash from a tag or branch or even from a hash """
		if version is None:
			version = 'HEAD'
		# for remote github, call "git ls-remote" because
		# "ssh github.com git rev-parse" cannot work with github
		if self.is_github_repo(uri):
			out = self.ls_remote(uri, version)
			if not out:
				return version
			re_rev = re.compile(r'^(?P<hash>\S+)\s+.*')
			match = re_rev.match(out)
			if match:
				return match.group('hash')


		if not version.endswith('^{}'):
			version += '^{}'
		(cmd_ret, out, err) = self.__git_cmd(cmd=['rev-parse', '--short', version ], \
						   uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)

                return out.strip()

        def tags(self, uri, version=None):
                """ if version is set returns tags associated to this version, else return every tag """
		if self.is_github_repo(uri):
			cmd = ['git', 'ls-remote', '--tags', uri]
			(cmd_ret, out, err) = self.__run_cmd(cmd)
		else:
		 	cmd = ['show-ref', '--tags', '--dereference']
			(cmd_ret, out, err) = self.__git_cmd(uri, cmd)

                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)

		if version:
			if not self.is_github_repo(uri):
				version = self.get_hash(uri, version)
			tags = []
			for t in out.splitlines():
				if t.startswith(version) or t.endswith(version):
					match = re_ref_tag_split.match(t)
					if match:
						tags.append(match.group('tag'))
			return tags
		else:
			tags = {}
			for t in out.splitlines():
					match = re_ref_tag_split.match(t)
					if match:
						tags[match.group('tag')] = match.group('hash')
			return tags

        def tag(self, uri, version, tag, message=None):
                cmd = ['tag', '-a', tag, version]
                if message is not None:
                        cmd += ['-m', '\'%s\'' % message]
                else:
                        cmd += ['-m', '']

                (cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)

        def add(self, uri, files):
                cmd = ['add']
                if type(files) is str:
                        cmd.append(files)
                else:
                        cmd += files
                (cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)

        def rm(self, uri, files):
                cmd = ['rm']
                if type(files) is str:
                        cmd.append(files)
                else:
                        cmd += files
                (cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)

        def commit(self, uri, files=None, message=None):
                cmd = ['commit']

                if message is not None:
                        cmd += ['-m', message]

                if type(files) is str:
                        cmd.append(files)
                elif files is not None:
                        cmd += files

                (cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)

        def merge_base(self, uri, reva, revb):
		(cmd_ret, out, err) = self.__git_cmd(cmd=['merge-base', reva, revb], uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)
                return out.strip()
              
        def log(self, uri, rev=None, template=None, branch=None):
                cmd = ['log']
                
                cmd.append('--no-merges')
                
                if rev:
                        cmd.append(rev)
                if template:
                        cmd += ['--format=%s' % template]
                if branch:
                        cmd += ['--branches=%s' % branch]
                
                (cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)
                return out

        def diff(self, uri, rev=None, file=None):
                cmd = ['diff']

                if rev:
                        cmd.append(rev)
                if file:
                        cmd += ['--',file]
                
                (cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)
                return out

        def ls_remote(self, uri, rev=None):
		cmd = []
                cmd += ['ls-remote', uri]

		if self.is_github_repo(uri):
			cmd.insert(0, 'git')
			(cmd_ret, res, err) = self.__run_cmd(cmd)
			if rev and rev in res:
				for ref in res.splitlines():
					if rev in ref:
						out = ref
			else:
				out = res
		else:
                	if rev:
                        	cmd.append(rev)
			(cmd_ret, out, err) = self.__git_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='Git command error', error_log=err)
                return out

#       FIXME/TODO rename and reimplement LATER
#        def push(self, uri, rev=None, dest=None):
#        def pull(self, uri, rev=None, src=None):
#        def update(self, uri, rev=None, clean=False):


