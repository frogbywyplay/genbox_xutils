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
import sys, os, re, shutil

from os.path import realpath, dirname
from subprocess import Popen, PIPE

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, os.path.join(curr_path, '..'))

import xutils.scm
import xutils.ebuild.ebuild_scm as b
from xutils.xerror import XUtilsError

EBUILD_TMP = curr_path + '/ebuilds/'
CURR_EBUILD = "github-test-0.0.1.0.ebuild"


tested_modules=[ 'xutils.ebuild' ]
class ebuildTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))
		self.uri = 'git@github.com:ptisserand/hello-test-to-remove.git'
		self.branch = 'master'
		self.revision = 'de39571'

        def testEbuildType(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.assertTrue(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.assertEqual(eb.get_type(), 'git')

        def testEbuildVersion(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.assertEqual(eb.get_version(), self.revision)

        def testEbuildName(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.assertEqual(eb.get_name(), CURR_EBUILD[:-7])
                self.assertTrue(eb.is_template())
                eb.set_version('0.0.2', check=True)
                self.assertEqual(eb.get_uri(), self.uri)
                self.assertEqual(eb.get_name(), 'github-test-0.0.2')
                self.assertTrue(not eb.is_template())
                eb.set_version('0.0.1')
                self.assertEqual(eb.get_name(), 'github-test-0.0.1')
	
	def testEbuildUserName(self):
		eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
		res = 0
		self.assertRaises(XUtilsError, eb.set_version, '35', check=False, name='user:1.2.0_beta')
		eb.set_version('f725a0f', check=False, name='user:1.2.0')
		self.assertEqual(eb.get_name(), 'github-test-1.2.0')
                
                eb.set_version('092ccbe0019a6eefa38edb2d4272017a96febbe2', check=False, name='user:1.3.0')
		self.assertEqual(eb.get_name(), 'github-test-1.3.0')

        def testEbuildError(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                res = 0
                try:
                        eb.set_version('35', check=False, name='pouet')
                except XUtilsError, e:
                        self.assertTrue(str(e).startswith("'pouet' naming scheme is not supported"), 'wrong error: %s' % str(e))
                        res = 1
                self.assertTrue(res == 1, 'An error should have been raised')

                res = 0
                try:
                        eb.set_version('35_beta42', check=False, name='tag')
                except XUtilsError, e:
                        self.assertTrue(str(e).startswith('Can\'t rename ebuild with'), 'wrong error: %s' % str(e))
                        res = 1
                self.assertTrue(res == 1, 'An error should have been raised')

                res = 0
                try:
                        eb.set_version(None, check=False, name='tag')
                except XUtilsError, e:
                        self.assertTrue(str(e).startswith('Can\'t rename ebuild when no tag'), 'wrong error: %s' % str(e))
                        res = 1
                self.assertTrue(res == 1, 'An error should have been raised')

        def testEbuildURI(self):
		"""
		Get EGIT_REPO_URI from ebuild
		"""
		eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
		self.assertEqual(eb.get_uri(), self.uri)

        def testEbuildBranch(self):
		"""
		Get EGIT_BRANCH from ebuild
		"""
		eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
		self.assertEqual(eb.get_branch(), self.branch)

        def testEbuildLatest(self):
		"""
		Get hash (SHA1) revision of HEAD for ebuild
		(clone repo locally to check that revision is valid)
		"""
		eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)

		# setup
		destination = '/tmp/' + eb.get_name()
		if os.path.exists(destination):
			shutil.rmtree(destination) # 'git clone' requires an empty directory
		os.makedirs(destination)
		command = [ 'git', 'clone', self.uri, destination ]
                p = Popen(command, env={
				'LC_ALL' : 'C',
				'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK')
				},
				stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
		savedPath = os.getcwd()
		os.chdir(destination)
		gitcmd = xutils.scm.create_git_cmd(destination)
		head_hashes = gitcmd.get_hash('HEAD')

		#isolate hash
		re_hash = re.compile('^(?P<hash>\S+)\s+\S+$')
		for line in head_hashes.splitlines():
			match = re_hash.match(line)
			head = match.group('hash') if match else ''
			break
		match = re_hash.match(eb.get_latest())
		latest = match.group('hash') if match else ''

		# test
		self.assertEqual(latest, head)

		# clean
		shutil.rmtree(destination)
		os.chdir(savedPath)

if __name__ == "__main__":
        unittest.main()

