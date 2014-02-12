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

import os, portage, re, sys

from subprocess import Popen, PIPE

from xutils.output import die
from xutils.xerror import XUtilsError

import exceptions

from xportage import XPortage, pkgsplit, ver_regexp

EBUILD_VAR_REGEXP=r'^\s*(?P<def>:\s+\${)?(?P<var>%s)(?(def):)=(?P<dbl>\")?(?P<value>(?:[^\\"]|\\.)*)(?(dbl)\")(?(def)})\s*(?:#.*)?$'
EBUILD_VAR_DEFTPL=': ${%s:="%s"}\n'

re_has_vars = re.compile(r'(?:[^\\]|^)\$(?P<acc>{)?[^\s]+(?(acc)})')
re_ignore_line = re.compile(r'(^$)|(^(\t)*#)')

def ebuild_match(file, match_func, all=False):
        if type(file) == str: # We need to read the file
                if not os.path.isfile(file):
                        die("Can't find %s" % file)
                fdin = open(file, "r")
                file = fdin.readlines()
                fdin.close()
        matches = None
        for line in file:
                if not re_ignore_line.match(line):
                        match = match_func(line)
                        if match and not all:
                                return match
                        elif match:
                                if not matches:
                                    matches = [ match ]
                                else:
                                    matches.append(match)
        return matches

class XEbuild(object):
        def __init__(self, file, buffer=None):
                if not file:
                        raise XUtilsError("a File must be provided")

                self.path = os.path.dirname(os.path.abspath(file)) + "/"
                self.buffer = buffer
                self.file = file

                name = os.path.basename(file)
                if not name.endswith(".ebuild"):
                        raise XUtilsError("The file is not an ebuild file")
                self._pkgsplit(name[:-7])

        def _read_file(self, file=None):
                if not file:
                        file = self.file

                if not os.path.isfile(file):
                        raise XUtilsError("Can't find %s" % file)
                self.file = file
                fdin = open(file, 'r')
                self.buffer = fdin.readlines()
                fdin.close()

        def _pkgsplit(self, name):
                split = pkgsplit(name)

                if not split:
                        raise XUtilsError('Can\'t split ebuild name')

                self.pn = split[0]
                if split[2] == "r0":
                        self.pr = None
                else:
                        self.pr = split[2]

                match = ver_regexp.match(split[1])
                if not match or not match.groups():
                        raise XUtilsError("syntax error in version: %s" % split[1])
                if match.group(1):
                        # cvs ebuild (unsupported in genbox)
                        raise XUtilsError("unsupported ebuild (cvs)")
                self.pv = { 'number' : [match.group(2)] }
                if len(match.group(3)):
                        self.pv['number'].extend(match.group(3)[1:].split("."))
                # ebuild revision with a [a-z] letter (empty string for others)
                self.pv['letter'] = match.group(5)
                # package suffix or empty string
                self.pv['suffix'] = match.group(6)

        def expand_vars(self, line):
                if not re_has_vars.search(line):
                        return line

                env = {
                        'PN' : self.pn,
                        'PV' : '%s%s%s' % (".".join(self.pv['number']),
                                self.pv['letter'], self.pv['suffix'])
                      }

                env['P'] = '%s-%s' % (env['PN'], env['PV'])

                if self.pr:
                        env['PR'] = self.pr
                        env['PVR'] = "%s-%s" % (env['PV'], self.pr)
                else:
                        env['PR'] = ""
                        env['PVR'] = env['PV']


                env['PF'] = '%s-%s' % (env['PN'], env['PVR'])
                env['CATEGORY'] = self.get_category()

		portage = XPortage(os.getenv('ROOT', '/'))

                if os.environ.has_key("EHG_BASE_URI"):
                    env['EHG_BASE_URI'] = os.environ['EHG_BASE_URI']
		else:
		    env['EHG_BASE_URI'] = portage.config["EHG_BASE_URI"]

                if os.environ.has_key("EGIT_BASE_URI"):
                    env['EGIT_BASE_URI'] = os.environ['EGIT_BASE_URI']
		else:
		    env['EGIT_BASE_URI'] = portage.config["EGIT_BASE_URI"]

		del portage

                cmd = Popen("echo -n \"%s\"" % line, bufsize=0,
                      shell=True, cwd=None, env=env, stdout=PIPE, stderr=PIPE)
                out, err = cmd.communicate()
                if cmd.returncode != 0:
                        raise XUtilsError("Something went wrong while expanding variables: \"%s\"" % err)
                return out

        def get_var(self, var_regex, all=False, dict=False):
                if not self.buffer:
                        raise XUtilsError("The file hasn't been loaded")

                if not var_regex:
                        return None
                elif type(var_regex) == str:
                        var_regex = re.compile(EBUILD_VAR_REGEXP % var_regex)

                match = ebuild_match(self.buffer, var_regex.search, all)
                if not match:
                        return None
                if all:
                        res = []
                        for m in match:
                                if dict:
                                        d = m.groupdict()
                                        d.pop('def')
                                        d.pop('dbl')
                                        d['value'] = self.expand_vars(d['value'])
                                        res.append(d)
                                else:
                                        res.append(self.expand_vars(m.group('value')))
                        return res
                elif dict:
                        d = match.groupdict()
                        d.pop('def')
                        d.pop('dbl')
                        d['value'] = self.expand_vars(d['value'])
                        return d
                else:
                        return self.expand_vars(match.group('value'))

        def get_name(self):
                name = '%s-%s%s%s' % (self.pn, ".".join(self.pv['number']), \
                        self.pv['letter'], self.pv['suffix'])
                if self.pr:
                        name += '-%s' % self.pr
                return name

        def get_category(self):
                return os.path.basename(os.path.dirname(self.path.rstrip('/')))

        def get_cpv(self):
                return '%s/%s' % (self.get_category(), self.get_name())

        def info(self):
                return "    %-15s: %s\n" % ('ebuild', self.get_name())

        def write(self, overwrite=False):
                new_ebuild = '%s%s.ebuild' % (self.path, self.get_name())
                if not overwrite and os.path.isfile(new_ebuild):
                        raise XUtilsError('Ebuild exists', num=1)
                fdout = open(new_ebuild, "w")
                for line in self.buffer:
                        fdout.write(line)
                fdout.close()
                del fdout

