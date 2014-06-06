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

'''Unittests for the git command class - xutils.scm.GitCmd
using a local and a remote repositories.

In theory, there shouldn't be and difference in accessing,
but it isn't possible to resolve arbitrary hash in the case of
a remote repository, only those informed by 'git ls-remote'.'''

import unittest
import sys, os, re

from os.path import realpath, dirname, exists

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, os.path.join(curr_path, '..'))
from xutils.scm.gitcmd import is_remote, create_cmd
from xutils import XUtilsError

# URL for the local git repo
URI_LOCAL = os.path.join(curr_path, 'scm_test/repo')

# URL for the remote git repo
URI_REMOTE = 'git@gitlab.wyplay.int:tools/genbox_xutils.git'


class LocalGitTester(unittest.TestCase):
	'''Testing GitCmd class using a local git repository.'''

	def cleanup_dirs(self):
		'''Erase all temporary dirs if any.'''
		self.assertEqual(os.system('rm -rf %s' % URI_LOCAL), 0)

        def setUp(self):
		'''Setting up the local repository.'''
		# before creating dirs, we need to remove them...
		self.cleanup_dirs()

		os.makedirs(URI_LOCAL)
		self.assertEqual(os.system('cd %s; git init' % URI_LOCAL), 0)
		self.assertEqual(os.system('''cd %s; echo "[user]
name = Test
email = hg@wyplay.com
" >> .git/config''' % URI_LOCAL), 0)
		self.assertEqual(os.system('echo 42 > %s/test' % URI_LOCAL), 0)

		# Test Target!!!
		self.cmd = create_cmd(URI_LOCAL)

		self.cmd.add(os.path.join(URI_LOCAL, 'test'))
		self.cmd.commit(message='adding_test')
		self.first_hash = self.cmd.get_hash('master')
		self.cmd.tag(self.first_hash, 'test_tag')
		self.cmd.tag(self.first_hash, 'test_tag_with_message', 'this is a message')

	def tearDown(self):
		self.cleanup_dirs()

	def testget_hash_first_hash(self):
		self.assertEqual(self.cmd.get_hash(self.first_hash), self.first_hash)

	def testget_hash_master(self):
		self.assertEqual(self.cmd.get_hash('master'), self.first_hash)

	def testget_hash_HEAD(self):
		self.assertEqual(self.cmd.get_hash('HEAD'), self.first_hash)

	def testget_hash_test_tag_deref(self):
		self.assertEqual(self.cmd.get_hash('test_tag^{}'), self.first_hash)

	def testget_hash_test_tag_deref_commit(self):
		self.assertEqual(self.cmd.get_hash('test_tag^{commit}'), self.first_hash)

	def testget_hash_test_tag_with_message_deref(self):
		self.assertEqual(self.cmd.get_hash('test_tag_with_message^{}'), self.first_hash)

	def testget_hash_test_tag_with_message_deref_commit(self):
		self.assertEqual(self.cmd.get_hash('test_tag_with_message^{commit}'), self.first_hash)

	def testTags4test_tag(self):
		self.assertEqual(self.cmd.tags('test_tag'), ['test_tag'])

	def testTags4None(self):
		tags = self.cmd.tags()
		self.assertTrue('test_tag_with_message' in tags)
		self.assertTrue('test_tag_with_message^{}' in tags)
		self.assertTrue('test_tag' in tags)
		self.assertTrue('test_tag^{}' in tags)
		self.assertTrue('HEAD' in tags)

	def testRemove(self):
		self.assertEqual(os.system('ls %s/test' % URI_LOCAL), 0)
		self.cmd.rm(os.path.join(URI_LOCAL, 'test'))
		self.cmd.commit(message='removing_test')
		self.assertNotEqual(os.system('ls %s/test' % URI_LOCAL), 0)

	def testMerge_base_one_branch(self):
		hash1 = self.cmd.get_hash('HEAD')
		self.assertEqual(os.system('cd %s; echo a > a' % URI_LOCAL), 0)
		self.cmd.add(os.path.join(URI_LOCAL, 'a'))
		self.cmd.commit(message='a_added')
		hash2 = self.cmd.get_hash('HEAD')
		self.assertNotEqual(hash1, hash2)
		self.assertEqual(hash1, self.cmd.merge_base(hash1, hash2))
		self.assertEqual(hash1, self.cmd.merge_base(hash2, hash1))

	def create_branch_two(self):
		'''Creates branch 'two' and returns three different hashes:
		base, master, two.'''
		hash1 = self.cmd.get_hash('HEAD')
		self.assertEqual(os.system('cd %s; git branch two;' % URI_LOCAL), 0)
		self.assertEqual(os.system('cd %s; echo a > a' % URI_LOCAL), 0)
		self.cmd.add(os.path.join(URI_LOCAL, 'a'))
		self.cmd.commit(message='a_added')
		hash2 = self.cmd.get_hash('HEAD')

		self.assertEqual(os.system('cd %s; git checkout two;' % URI_LOCAL), 0)
		self.assertEqual(os.system('cd %s; echo a > b' % URI_LOCAL), 0)
		self.cmd.add(os.path.join(URI_LOCAL, 'b'))
		self.cmd.commit(message='b_added')
		hash3 = self.cmd.get_hash('HEAD')

		return (hash1, hash2, hash3)

	def testMerge_base_two_branches(self):
		(hash1, hash2, hash3) = self.create_branch_two()
		self.assertNotEqual(hash1, hash2)
		self.assertNotEqual(hash2, hash3)
		self.assertNotEqual(hash1, hash3)
		self.assertEqual(hash1, self.cmd.merge_base(hash1, hash2))
		self.assertEqual(hash1, self.cmd.merge_base(hash2, hash1))
		self.assertEqual(hash1, self.cmd.merge_base(hash1, hash3))
		self.assertEqual(hash1, self.cmd.merge_base(hash2, hash3))

	def testResolve_abracadabra(self):
		self.assertEqual(self.cmd.get_hash('abracadabra'), None)

	def testContains_first_hash(self):
		self.assertEqual(self.cmd.contains(self.first_hash), ['master'])

	def testContains_test_tag(self):
		self.assertEqual(self.cmd.contains('test_tag'), ['master'])

	def testContains_test_tag_with_message(self):
		self.assertEqual(self.cmd.contains('test_tag_with_message'), ['master'])

	def testContains_branch_two(self):
		(hash1, hash2, hash3) = self.create_branch_two()
		self.assertEqual(self.cmd.contains(hash1), ['master', 'two'])
		self.assertEqual(self.cmd.contains(hash2), ['master'])
		self.assertEqual(self.cmd.contains(hash3), ['two'])
		self.assertEqual(self.cmd.contains('two'), ['two'])

	def testContains_abracadabra(self):
		self.assertEqual(self.cmd.contains('abracadabra'), [])

	def testCheck_revision_first_hash(self):
		self.assertTrue(self.cmd.check_revision(self.first_hash, 'master'))

	def testCheck_revision_branch_two(self):
		(hash1, hash2, hash3) = self.create_branch_two()
		self.assertTrue(self.cmd.check_revision(hash1, 'master'))
		self.assertTrue(self.cmd.check_revision(hash1, 'two'))
		self.assertTrue(self.cmd.check_revision(hash2, 'master'))
		self.assertFalse(self.cmd.check_revision(hash2, 'two'))
		self.assertFalse(self.cmd.check_revision(hash3, 'master'))
		self.assertTrue(self.cmd.check_revision(hash3, 'two'))

	def testCheck_revision_abracadabra_in_master(self):
		self.assertFalse(self.cmd.check_revision('abracadabra', 'master'))

	def testCheck_revision_abracadabra_in_abracadabra(self):
		self.assertRaises(XUtilsError, self.cmd.check_revision,
				'abracadabra', 'abracadabra')


class RemoteGitTester(unittest.TestCase):
	'''Testing GitCmd class using a remote git repository.'''

        def setUp(self):
		self.cmd = create_cmd(URI_REMOTE)

	def testResolve_tag_2_2_8(self):
		self.assertEqual(
			self.cmd.get_hash('2.2.8'),
			'6ef69a56d34286c757d2e0f30e45516c83349623')

	def testResolve_tag_2_2_8_deref(self):
		self.assertEqual(
			self.cmd.get_hash('2.2.8^{}'),
			'6ef69a56d34286c757d2e0f30e45516c83349623')

	def testResolve_HEAD(self):
		self.assertEqual(len(self.cmd.get_hash('HEAD')), 40)

	def testResolve_master(self):
		self.assertEqual(len(self.cmd.get_hash('master')), 40)

	def testResolve_tag_2_2_8_by_full_hash(self):
		self.assertEqual(
			self.cmd.get_hash('6ef69a56d34286c757d2e0f30e45516c83349623'),
			'6ef69a56d34286c757d2e0f30e45516c83349623')

	def testResolve_tag_2_2_8_by_short_hash(self):
		self.assertEqual(
			self.cmd.get_hash('6ef69'),
			'6ef69a56d34286c757d2e0f30e45516c83349623')

	def testResolve_short_master_hash(self):
		'''Using master hash to resolve from short hash.'''
		master_hash = self.cmd.get_hash('master')
		self.assertEqual(
			self.cmd.get_hash(master_hash[:6]),
			master_hash)

	def testResolve_short_master_hash_deref(self):
		master_hash = self.cmd.get_hash('master')
		first6letters = self.cmd.get_hash('master')[:6]
		self.assertEqual(
			self.cmd.get_hash(master_hash[:6] + '^{}'),
			master_hash)

	def testResolve_full_master_hash(self):
		master_hash = self.cmd.get_hash('master')
		self.assertEqual(
			self.cmd.get_hash(master_hash),
			master_hash)

	def testResolve_inner_part_master_hash(self):
		'''Using the middle of the master hash - testing matching start.'''
		master_hash = self.cmd.get_hash('master')
		self.assertEqual(self.cmd.get_hash(master_hash[10:16]), None)

	def testResolve_tag_2_2_11(self):
		self.assertEqual(
			self.cmd.get_hash('2.2.11'),
			'4ab9ef2e41f7a6e3f51813beb0a4eb4c6f240431')

	def testResolve_tag_2_2_11_deref(self):
		self.assertEqual(
			self.cmd.get_hash('2.2.11^{}'),
			'b2b28248853a89b4d5fce73a935bdc858f3686f6')

	def testResolve_abracadabra(self):
		self.assertEqual(
			self.cmd.get_hash('abracadabra'),
			None)

	def testTags(self):
		tags = self.cmd.tags()
		self.assertTrue('2.2.10' in tags)
		self.assertTrue('2.2.11' in tags)
		self.assertTrue('2.2.11^{}' in tags)
		self.assertTrue('2.2.8' in tags)
		self.assertTrue('2.2.9' in tags)

	def testTags_by_2_2_8(self):
		self.assertEqual(self.cmd.tags('2.2.8'), ['2.2.8', ])

	def testTags_by_6ef69(self):
		self.assertEqual(self.cmd.tags('6ef69'), ['2.2.8', ])

	def testCheck_revision_6ef69_in_master(self):
		self.assertTrue(self.cmd.check_revision('6ef69', 'master'))

	def testCheck_revision_2_2_8_in_master(self):
		self.assertTrue(self.cmd.check_revision('2.2.8', 'master'))

	def testCheck_revision_abracadabra_in_master(self):
		self.assertFalse(self.cmd.check_revision('abracadabra', 'master'))

	def testCheck_revision_abracadabra_in_abracadabra(self):
		self.assertRaises(XUtilsError, self.cmd.check_revision,
				'abracadabra', 'abracadabra')


class IsRemoteTester(unittest.TestCase):
	'''Testing is_remote(uri) function.'''

	def testAbracadabra(self):
		self.assertRaises(XUtilsError, is_remote, "abracadabra")

	def testURI_LOCAL(self):
		self.assertFalse(is_remote(curr_path))

	def testURI_REMOTE(self):
		self.assertTrue(is_remote(URI_REMOTE))

	def testscp_like(self):
		self.assertTrue(is_remote("toto@tata.tutu:/ti/ti"))

	def testssh(self):
		self.assertTrue(is_remote("ssh://toto@tata.tutu:/ti/ti"))


if __name__ == "__main__":
        unittest.main()

