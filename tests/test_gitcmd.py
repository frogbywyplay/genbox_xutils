#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import unittest
import sys, os, re

from os.path import realpath, dirname, exists

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xutils.scm as s
from xutils import XUtilsError

SCM_DIR = curr_path + '/scm_test/repo1'
SCM_DIR2 = curr_path + '/scm_test/repo2'

class GitTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def setUp(self):
                os.system('rm -rf %s' % SCM_DIR)
                if not exists(curr_path + '/scm_test'):
                        os.makedirs(curr_path + '/scm_test')

        def testGit(self):
                if not exists(SCM_DIR):
                        os.makedirs(SCM_DIR)

                os.system('cd %s; git init' % SCM_DIR)
                cmd = s.GitCmd()

                os.system('echo 42 > %s/test' % SCM_DIR)
                try:
                        cmd.add(SCM_DIR, SCM_DIR + '/test')
                        cmd.commit(SCM_DIR, message='adding_test')
                        hash = cmd.get_hash(SCM_DIR, 'master')
                        cmd.tag(SCM_DIR, hash, 'test_tag')
                        cmd.tag(SCM_DIR, hash, 'test_tag_with_message', 'this is a message')
                        self.failUnlessEqual(cmd.tags(SCM_DIR, 'test_tag'),
                                ['test_tag'])
                        self.failUnlessEqual(cmd.tags(SCM_DIR, None).keys(),
                                ['test_tag_with_message', 'test_tag_with_message^{}','test_tag', 'test_tag^{}'])

                        self.failUnless(os.system('ls %s/test' % SCM_DIR) == 0)
                        cmd.rm(SCM_DIR, SCM_DIR + '/test')
                        cmd.commit(SCM_DIR, message='removing_test')
                        self.failUnless(os.system('ls %s/test' % SCM_DIR) != 0)
                except XUtilsError, e:
                        print e.get_error_log()
                        self.fail(str(e))

        def testGitSSH(self):
                cmd = s.GitCmd()
                try:
                        uri='ssh://git.wyplay.int/var/lib/git/kernel-wyplay-2.6.23.y.git'
                        self.failUnlessEqual(cmd.get_hash(uri, '35'), '5a97794d66909dbe3282062d7637705bcd352815')
                        #self.failUnless('35^{}' in cmd.tags(uri, '35'))
                except XUtilsError, e:
                        print e.get_error_log()
                        self.fail(str(e))
        
        def tearDown(self):
                os.system('rm -rf %s' % SCM_DIR)
                os.system('rm -rf %s' % SCM_DIR2)

if __name__ == "__main__":
        unittest.main()

