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

import sys, color

verbose_val = False

def verbose(enable):
        global verbose_val
        if enable == True:
                verbose_val = True
        else:
                verbose_val = False

def _print(str, eol=True, output=sys.stdout):
        print >>output, str,
        if eol:
                print >>output
        else:
                sys.stdout.flush()

def die(str=None, output=sys.stdout):
        if str is not None:
                _print(color.red(" * ") + str, False, output)
        sys.exit(1)

def warn(str, eol=True, output=sys.stdout):
        _print(color.yellow(" * ") + str, eol, output)

def error(str, eol=True, output=sys.stdout):
        _print(color.red(" * ") + str, eol, output)

def vinfo(str, eol=True, output=sys.stdout):
        global verbose_val
        if verbose_val:
                _print(color.green(" * ") + str, eol, output)

def info(str, eol=True, output=sys.stdout):
        _print(color.green(" * ") + str, eol, output)

def is_verbose():
        return verbose_val

def userquery(prompt, output=sys.stdout):
        _print(color.bold(prompt), False, output)
        _print('[%s/%s]' % (color.green('Yes'), color.red('No')), False, output)

        while True:
                res = raw_input()
                if not res or res.upper() == "YES":
                        return True
                elif res.upper() == "NO":
                        return False
                else:
                        _print("Sorry, response '%s' not understood." % res, True, output)

