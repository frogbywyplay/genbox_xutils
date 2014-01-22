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
import xutils.ebuild.ebuild_scm as b
from xutils.xerror import XUtilsError

EBUILD_TMP = curr_path + '/ebuilds/'
CURR_EBUILD = "git-test-1.0.0.0.ebuild"


tested_modules=[ 'xutils.ebuild' ]
class ebuildTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def testEbuildType(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnless(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.failUnlessEqual(eb.get_type(), 'git')

        def testEbuildVersion(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_version(), 'master')

        def testEbuildName(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_name(), CURR_EBUILD[:-7])
                self.failUnless(eb.is_template())
                eb.set_version('35', check=True)
                self.failUnlessEqual(eb.get_name(), 'git-test-35')
                self.failUnless(not eb.is_template())
                eb.set_version('34')
                self.failUnlessEqual(eb.get_name(), 'git-test-34')
                self.failUnlessEqual(eb.get_version(), eb.gitcmd.get_hash(eb.get_uri(), '34'))
                eb.get_latest()
	
	def testEbuildUserName(self):
		eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
		res = 0
		self.assertRaises(XUtilsError, eb.set_version, '35', check=False, name='user:1.2.0_beta')
		eb.set_version('35', check=False, name='user:1.2.0')
		self.assertEqual(eb.get_name(), 'git-test-1.2.0')
                
                eb.set_version('092ccbe0019a6eefa38edb2d4272017a96febbe2', check=False, name='user:1.3.0')
		self.assertEqual(eb.get_name(), 'git-test-1.3.0')

        def testEbuildError(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                res = 0
                try:
                        eb.set_version('35', check=False, name='pouet')
                except XUtilsError, e:
                        self.failUnless(str(e).startswith("'pouet' naming scheme is not supported"), 'wrong error: %s' % str(e))
                        res = 1
                self.failUnless(res == 1, 'An error should have been raised')

                res = 0
                try:
                        eb.set_version('35_beta42', check=False, name='tag')
                except XUtilsError, e:
                        self.failUnless(str(e).startswith('Can\'t rename ebuild with'), 'wrong error: %s' % str(e))
                        res = 1
                self.failUnless(res == 1, 'An error should have been raised')

                res = 0
                try:
                        eb.set_version(None, check=False, name='tag')
                except XUtilsError, e:
                        self.failUnless(str(e).startswith('Can\'t rename ebuild when no tag'), 'wrong error: %s' % str(e))
                        res = 1
                self.failUnless(res == 1, 'An error should have been raised')

if __name__ == "__main__":
        unittest.main()

