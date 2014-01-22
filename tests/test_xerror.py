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
import xutils.xerror as err

tested_modules=[ 'xutils.xerror' ]
class xerrorTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def testXerror(self):
                try:
                        raise err.XUtilsError(error='text', num=42, error_log='my log')
                except err.XUtilsError, e:
                        self.failUnlessEqual(e.get_error(), 'text')
                        self.failUnlessEqual(e.get_error_log(), 'my log')
                        self.failUnlessEqual(e.get_error_number(), 42)
                        self.failUnlessEqual(str(e), 'text')
                        self.failUnlessEqual(int(e), 42)

                try:
                        raise err.XUtilsError(error='text')
                except err.XUtilsError, e:
                        self.failUnlessEqual(e.get_error_log(), None)
                        self.failUnlessEqual(e.get_error_number(), 0)
                        self.failUnlessEqual(int(e), 0)


if __name__ == "__main__":
        unittest.main()

