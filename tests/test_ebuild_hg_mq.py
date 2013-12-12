#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
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
CURR_EBUILD = "portage-2.1.4.4.0.ebuild"
REPO_TMP = curr_path + '/repos'


tested_modules=[ 'xutils.ebuild' ]
class ebuildTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

	def setUp(self):
		self.env_bkup = os.environ.copy()
		os.mkdir(REPO_TMP + '/genbox')
		tt = tarfile.open(REPO_TMP + '/portage.tar.gz')
		tt.extractall(REPO_TMP + '/genbox')
		# use local repository
		os.environ['EHG_BASE_URI'] = 'file://%s' % REPO_TMP
	
	def tearDown(self):
		shutil.rmtree(REPO_TMP + '/genbox')
		os.environ = self.env_bkup.copy()

        def testEbuildType(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnless(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.failUnlessEqual(eb.get_type(), 'mercurial-mq')

        def testEbuildVersion(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_version(), ('sys-apps/portage-2.1.4.4', 'sys-apps/portage-2.1.4.4'))

        def testEbuildName(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_name(), CURR_EBUILD[:-7])
                eb.set_version(('6fcd3222e086', '2b4a3e216544'))
                self.failUnlessEqual(eb.get_name(), 'portage-2.1.4.4.1_p6')
                eb.set_version(('9ffd0e3a71ff', 'af417af1097c'))
                self.failUnlessEqual(eb.get_name(), 'portage-2.1.4.4.2_p7')
	
	def testEbuildUserName(self):
		eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
		eb.set_version(('9ffd0e3a71ff', 'af417af1097c'), name='user:2.1.4.6')
		self.assertEqual(eb.get_name(), 'portage-2.1.4.6')
	
if __name__ == "__main__":
        unittest.main()

