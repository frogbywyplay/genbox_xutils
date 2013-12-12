#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
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

