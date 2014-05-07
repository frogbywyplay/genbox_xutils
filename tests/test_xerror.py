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

	def testTextNumLog(self):
		try:
			raise err.XUtilsError(error='text', num=42, error_log='my log')
		except err.XUtilsError, e:
			self.assertEqual(e.get_error(), 'text')
			self.assertEqual(e.get_error_log(), 'my log')
			self.assertEqual(e.get_error_number(), 42)
			self.assertEqual(str(e), 'text (num=42): my log')
			self.assertEqual(int(e), 42)

	def testNoNum(self):
		try:
			raise err.XUtilsError(error='text', error_log='my log')
		except err.XUtilsError, e:
			self.assertEqual(e.get_error(), 'text')
			self.assertEqual(e.get_error_log(), 'my log')
			self.assertEqual(e.get_error_number(), 0)
			self.assertEqual(str(e), 'text: my log')
			self.assertEqual(int(e), 0)

	def testOnlyText(self):
		try:
			raise err.XUtilsError(error='text')
		except err.XUtilsError, e:
			self.assertEqual(e.get_error_log(), None)
			self.assertEqual(e.get_error_number(), 0)
			self.assertEqual(str(e), 'text')
			self.assertEqual(int(e), 0)

	def testRepr(self):
		from xutils.xerror import XUtilsError
		e = eval(repr(XUtilsError("Error", 123, "abc")))
		self.assertEqual(e.get_error_log(), "abc")
		self.assertEqual(e.get_error_number(), 123)
		self.assertEqual(str(e), 'Error (num=123): abc')
		self.assertEqual(int(e), 123)

	def testReprOnlyText(self):
		from xutils.xerror import XUtilsError
		e = eval(repr(XUtilsError("Error")))
		self.assertEqual(e.get_error_log(), None)
		self.assertEqual(e.get_error_number(), 0)
		self.assertEqual(str(e), 'Error')
		self.assertEqual(int(e), 0)

	def testReprNoNum(self):
		from xutils.xerror import XUtilsError
		e = eval(repr(XUtilsError("Error", error_log="abc")))
		self.assertEqual(e.get_error_log(), "abc")
		self.assertEqual(e.get_error_number(), 0)
		self.assertEqual(str(e), 'Error: abc')
		self.assertEqual(int(e), 0)

if __name__ == "__main__":
        unittest.main()

