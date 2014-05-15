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

import os, os.path
import shutil
import sys

from os.path import realpath, dirname, exists

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')

import xutils.scm
from subprocess import Popen, PIPE

DEST = '/tmp/repo.git'

class GithubTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))
		self.has_github = None
		self.uri = 'git@github.com:ptisserand/hello-test-to-remove.git'
		self.branch = 'master'
		self.revision = 'de39571'
		self.tag = '0.0.1' # tag associated to self.revision

	def setUp(self):
		if self.__github_check():
			self.__clone_repo()
		self.gitcmd = xutils.scm.create_git_cmd(DEST)

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
		hash = self.gitcmd.get_hash(self.tag)
		self.assertEqual(self.revision, hash[:7])

        def testGithubTags(self):
		"""
		List tags for a given github repo
		"""
		if not self.__github_check():
			return
		tags = self.gitcmd.tags()
		tag = self.gitcmd.tags(self.revision)
		self.assertEqual({'0.0.1': 'de3957100582c76727505623a4c846f5097e5308', '0.0.2': 'f725a0f47fc6c0aa85792d63da079be00d3a46da'}, tags)
		self.assertEqual([self.tag], tag)

        def testGithubLog(self):
		"""
		Get a log message from a github repo
		"""
		if not self.__github_check():
			return
		all_log = self.gitcmd.log()
		log = self.gitcmd.log(self.tag)
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
		diff = self.gitcmd.diff(self.revision)
		self.assertTrue(diff)
		self.assertTrue('Just for test' in diff)


        def testGithubTags(self):
		"""
		Get a revision (SHA1) from a github repo
		"""
		if not self.__github_check():
			return
		local_head = self.gitcmd.get_hash('HEAD')
		local_tag = self.gitcmd.get_hash(self.tag)
		tags = self.gitcmd.tags()
		self.assertTrue(self.tag in tags)
		self.assertEqual(tags[self.tag], local_tag)
		self.assertTrue('HEAD' in tags)
		self.assertEqual(tags['HEAD'], local_head)

if __name__ == "__main__":
        unittest.main()

