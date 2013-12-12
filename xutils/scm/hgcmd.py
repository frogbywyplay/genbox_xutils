#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import re, os

from subprocess import Popen, PIPE

from xutils import XUtilsError
from mercurial import hg, ui, __version__
if __version__.version > "1.9.1":
    from mercurial.hg import _peerlookup as hg_lookup
else:
    from mercurial.hg import _lookup as hg_lookup

class HGCmd(object):
        __uri_split = re.compile(r'(?:.*://)?([^/]*)/(.*)')
        # needed to read configuration
        hg.extensions.loadall(ui.ui())
        
        def __hg_ssh_cmd(self, host, path, cmd):
                command = ['/usr/bin/ssh', host, 'hg', '-R', path] + cmd
                p = Popen(command, env={
                                        'LC_ALL' : 'C',
                                        'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK', '')
                                       },
                          stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
                return (p.returncode, stdout, stderr)

        def __hg_file_cmd(self, uri, cmd):
                if uri.startswith('file://'):
                        uri = uri[7:]

                command = ['hg', '-R', uri] + cmd
                p = Popen(command, env={
                                        'LC_ALL' : 'C',
                                        'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK', '')
                                       },
                          stdout=PIPE, stderr=PIPE, cwd=uri)
                (stdout, stderr) = p.communicate()
                return (p.returncode, stdout, stderr)

        def __hg_cmd(self, uri, cmd):
                # handle genschemes
                scheme = hg_lookup(uri)
                if hasattr(scheme, 'get_url'):
                        uri = scheme.get_url(uri)
                if uri.startswith('ssh://'):
                        (url, path) = HGCmd.__uri_split.match(uri).groups()
                        return self.__hg_ssh_cmd(host=url, path=path, cmd=cmd)
                elif uri.startswith('http://') or uri.startswith('https://'):
                        raise XUtilsError(error='http proto not supported in HGCmd')
                else:
                        return self.__hg_file_cmd(uri=uri, cmd=cmd)

        def identify(self, uri, version):
                (cmd_ret, out, err) = self.__hg_cmd(cmd=['identify', '-r', version, \
                                                   '-i', '-n', '-b'], \
                                                   uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

                try:
                        (hash, number, branch) = out.split()
                except ValueError:
                        raise XUtilsError(error='HG command error', error_log=err)

                return {
                        'hash' : hash,
                        'branch' : branch,
                        'num' : number
                       }

        def tags(self, uri, version=None):
                if version:
                        (cmd_ret, out, err) = self.__hg_cmd(cmd=['identify', '-r', version, \
                                                           '-t'], uri=uri)
                        if cmd_ret != 0:
                                raise XUtilsError(error='HG command error', error_log=err)
                        # Fixme remove 'tip'
                        ret = out.split()
                        ret.sort()
                        return ret
                else:
                        re_tag_split = re.compile('^(?P<tag>[^\s]+)\s+[0-9]+:(?P<hash>.*)')
                        (cmd_ret, out, err) = self.__hg_cmd(cmd=['tags'], uri=uri)

                        if cmd_ret != 0:
                                raise XUtilsError(error='HG command error', error_log=err)

                        tags = {}
                        for line in out.splitlines():
                                match = re_tag_split.match(line)
                                if not match:
                                        continue
                                tags[match.group('tag')] = match.group('hash')
                        return tags 


        def tag(self, uri, version, tag, message=None):
                cmd = ['tag', '-r', version]
                if message is not None:
                        cmd += ['-m', '\'%s\'' % message]
                cmd.append(tag)

                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def add(self, uri, files):
                cmd = ['add']
                if type(files) is str:
                        cmd.append(files)
                else:
                        cmd += files
                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def rm(self, uri, files):
                cmd = ['rm']
                if type(files) is str:
                        cmd.append(files)
                else:
                        cmd += files
                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def commit(self, uri, files=None, message=None):
                cmd = ['commit']

                if message is not None:
                        cmd += ['-m', message]

                if type(files) is str:
                        cmd.append(files)
                elif files is not None:
                        cmd += files

                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def push(self, uri, rev=None, dest=None):
                cmd = ['push']

                if rev is not None:
                        cmd += ['-r', rev]
                if dest is not None:
                        cmd.append(dest)

                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def pull(self, uri, rev=None, src=None):
                cmd = ['pull']

                if rev is not None:
                        cmd += ['-r', rev]
                if src is not None:
                        cmd.append(src)

                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def update(self, uri, rev=None, clean=False):
                cmd = ['update']

                if clean:
                        cmd.append('-C')
                if rev is not None:
                        cmd += ['-r', rev]

                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def addremove(self, uri, files=None):
                cmd = ['addremove']

                if type(files) is str:
                        cmd.append(files)
                elif files is not None:
                        cmd += files

                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)

        def log(self, uri, rev=None, template=None, branch=None):
                cmd = ['log']
                
                cmd.append('--no-merges')
                
                if rev:
                        cmd += ['-r', rev]
                if template:
                        cmd += ['--template', '%s' % template]
                if branch:
                        cmd += ['-b', '%s' % branch]
                
                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)
                return out

        def diff(self, uri, rev=None, file=None):
                cmd = ['diff']

                if rev:
                        cmd += ['-r', rev]
                if file:
                        cmd.append(file)
                
                (cmd_ret, out, err) = self.__hg_cmd(cmd=cmd, uri=uri)
                if cmd_ret != 0:
                        raise XUtilsError(error='HG command error', error_log=err)
                return out
