#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import unittest
import sys, os, re, shutil

from os.path import realpath, dirname
from subprocess import Popen, PIPE

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
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
                self.failUnless(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.failUnlessEqual(eb.get_type(), 'git')

        def testEbuildVersion(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_version(), self.revision)

        def testEbuildName(self):
                eb = b.ebuild_factory(EBUILD_TMP + CURR_EBUILD)
                self.failUnlessEqual(eb.get_name(), CURR_EBUILD[:-7])
                self.failUnless(eb.is_template())
                eb.set_version('0.0.2', check=True)
                self.failUnlessEqual(eb.get_name(), 'github-test-0.0.2')
                self.failUnless(not eb.is_template())
                eb.set_version('0.0.1')
                self.failUnlessEqual(eb.get_name(), 'github-test-0.0.1')
	
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
		gitcmd = xutils.scm.GitCmd()
		head_hashes = gitcmd.get_hash(uri=destination, version='HEAD')

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

