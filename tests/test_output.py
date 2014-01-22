#!/usr/bin/python
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

import unittest
import sys, os, re

from os.path import realpath, dirname

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xutils.output as c

TMP_FILE= curr_path + '/temp_file'

class configTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def testOutput(self):
                (fd_in, fd_out) = os.pipe()
                sys.stdin = os.fdopen(fd_in, 'r')

                os.write(fd_out, 'Yes\n')
                self.failUnlessEqual(c.userquery('say Yes?'), True)
                print "Yes"

                os.write(fd_out, 'No\n')
                self.failUnlessEqual(c.userquery('say No?'), False)
                print "No"

                os.write(fd_out, 'YeS\n')
                self.failUnlessEqual(c.userquery('say YeS?'), True)
                print "YeS"

                os.write(fd_out, '\n')
                self.failUnlessEqual(c.userquery('say nothing?'), True)
                print ""

                os.write(fd_out, 'maybe\nNo\n')
                self.failUnlessEqual(c.userquery('say maybe then No?'), False)
                print 'maybe\nNo\n'

                os.close(fd_out)

if __name__ == "__main__":
        unittest.main()

