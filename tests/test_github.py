#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import unittest

import os, os.path
import shutil
import sys
import xutils.scm
from subprocess import Popen, PIPE

DEST = '/tmp/repo.git'

class GithubTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))
		self.has_github = None
		self.gitcmd = xutils.scm.GitCmd()
		self.uri = 'git@github.com:ptisserand/hello-test-to-remove.git'
		self.branch = 'master'
		self.revision = 'de39571'
		self.tag = '0.0.1' # tag associated to self.revision

	def setUp(self):
		if self.__github_check():
			self.__clone_repo()

	def tearDown(self):
		if self.__github_check():
			self.__clear_repo()

	def __clone_repo(self, where = DEST):
		if os.path.exists(where):
			shutil.rmtree(where) # 'git clone' requires an empty directory
		os.makedirs(where)
		command = [ 'git', 'clone', self.uri, where ]
                p = Popen(command, env={
				'LC_ALL' : 'C',
				'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK')
				},
				stdout=PIPE, stderr=PIPE)
                (stdout, stderr) = p.communicate()
                if 0 != p.wait():
                      raise Exception("Failed to clone repository: ", stderr)
		self.savedPath = os.getcwd()
		os.chdir(where)

	def __clear_repo(self, where = DEST):
		os.chdir(self.savedPath)
		if not os.path.exists(where):
			return
		shutil.rmtree(where)

	def __github_check(self):
		"""
		Check if user can connect to github.com
		If not, these tests are quite useless
		"""
		if self.has_github is not None:
			return self.has_github
		command = [ 'ssh', '-T', 'git@github.com' ]
                p = Popen(command, env={
				'LC_ALL' : 'C',
				'SSH_AUTH_SOCK' : os.getenv('SSH_AUTH_SOCK')
				},
				stdout=PIPE, stderr=PIPE)
                ret = p.wait()
                # github return 1 if OK
                self.has_github = ret == 1
		return self.has_github

        def testGithubGetHash(self):
		"""
		Get hash from a local github repo
		"""
		if not self.__github_check():
			return
		hash = self.gitcmd.get_hash(DEST, self.tag)
		self.assertEqual(self.revision, hash[:7])

        def testGithubTags(self):
		"""
		List tags for a given github repo
		"""
		if not self.__github_check():
			return
		tags = self.gitcmd.tags(DEST)
		tag = self.gitcmd.tags(DEST, self.revision)
		self.assertEqual({'0.0.1': 'de3957100582c76727505623a4c846f5097e5308', '0.0.2': 'f725a0f47fc6c0aa85792d63da079be00d3a46da'}, tags)
		self.assertEqual([self.tag], tag)

        def testGithubLog(self):
		"""
		Get a log message from a github repo
		"""
		if not self.__github_check():
			return
		all_log = self.gitcmd.log(DEST)
		log = self.gitcmd.log(DEST, self.tag)
		self.assertTrue(all_log)
		self.assertTrue('Nov 5 10:37:05' in all_log)
		self.assertTrue(log)
		self.assertTrue(log.startswith('commit %s' % self.revision))

        def testGithubDiff(self):
		"""
		Get a patch (diff) from a github repo
		"""
		#TODO: test with a file / test without file or revision supplied
		if not self.__github_check():
			return
		diff = self.gitcmd.diff(DEST, self.revision)
		self.assertTrue(diff)
		self.assertTrue('Just for test' in diff)


        def testGithubLsremote(self):
		"""
		Get a revision (SHA1) from a github repo
		"""
		if not self.__github_check():
			return
		local_head = self.gitcmd.get_hash(DEST, 'HEAD')
		local_tag = self.gitcmd.get_hash(DEST, self.tag)
		remote_head = self.gitcmd.ls_remote(DEST)
		remote_tag = self.gitcmd.ls_remote(DEST, self.tag)
		self.assertEqual(local_head[:7], remote_head[:7])
		self.assertEqual(local_tag[:7], remote_tag[:7])

if __name__ == "__main__":
        unittest.main()

