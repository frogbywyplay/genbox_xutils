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
# these 2 imports are required to create xutils HG repository during test suite
import tarfile
import shutil

from os.path import realpath, dirname

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xutils.ebuild.ebuild_scm as b
from xutils.xerror import XUtilsError

EBUILD_TMP = curr_path + '/ebuilds/'
CURR_EBUILD = "xutils-1.0.0.0.ebuild"
REPO_TMP = curr_path + '/repos'


tested_modules=[ 'xutils.ebuild' ]
class ebuildTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

	def setUp(self):
		self.env_bkup = os.environ.copy()
		os.mkdir(REPO_TMP + '/genbox')
		os.mkdir(REPO_TMP + '/genbox/genbox-tools')
		tt = tarfile.open(REPO_TMP + '/xutils.tar.gz')
		tt.extractall(REPO_TMP + '/genbox/genbox-tools')
		# use local repository
		os.environ['EHG_BASE_URI'] = 'file://%s' % REPO_TMP
	
	def tearDown(self):
		shutil.rmtree(REPO_TMP + '/genbox')
		os.environ = self.env_bkup.copy()
	
        def testEbuildType(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnless(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.failUnlessEqual(eb.get_type(), 'mercurial')

        def testEbuildVersion(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_version(), 'default')

        def testEbuildName(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_name(), CURR_EBUILD[:-7])
                eb.set_version('7f5c907ea128')
                self.failUnlessEqual(eb.get_name(), 'xutils-1.0.0.116')
                eb.set_version('dfac7eb4cbe6')
                self.failUnlessEqual(eb.get_name(), 'xutils-1.0.0.117')
	
	def testEbuildUserName(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                eb.set_version('dfac7eb4cbe6', name='user:1.2.3')
                self.assertEqual(eb.get_name(), 'xutils-1.2.3')
	
if __name__ == "__main__":
        unittest.main()

