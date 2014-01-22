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
import xutils.scm as s
from xutils import XUtilsError

SCM_DIR = curr_path + '/scm_test/repo1'
SCM_DIR2 = curr_path + '/scm_test/repo2'

class HGTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def setUp(self):
                os.system('rm -rf %s' % SCM_DIR)
                if not os.path.exists(curr_path + '/scm_test'):
                        os.makedirs(curr_path + '/scm_test')

        def testHG(self):
                os.system('hg init %s' % SCM_DIR)
                hgcmd = s.HGCmd()
                self.failUnlessEqual(hgcmd.identify(SCM_DIR, 'tip'),
                        {'num': '-1', 'hash': '000000000000', 'branch': 'default'})

                os.system('echo 42 > %s/test' % SCM_DIR)
                hgcmd.add(SCM_DIR, SCM_DIR + '/test')
                hgcmd.commit(SCM_DIR, message='adding_test')
                hgcmd.tag(SCM_DIR, '0', 'test_tag')
                self.failUnlessEqual(hgcmd.tags(SCM_DIR, 'test_tag'),
                        ['test_tag'])

                hgcmd.tag(SCM_DIR, '0', 'test_tag2', 'titi')
                self.failUnlessEqual(hgcmd.tags('file://' + SCM_DIR).keys(),
                        ['test_tag2', 'tip', 'test_tag'])

                os.system('echo 43 > %s/test' % SCM_DIR)
                hgcmd.commit(SCM_DIR, message='modify_test')
                self.failUnlessEqual(hgcmd.tags(SCM_DIR, '0'), ['test_tag', 'test_tag2'])

        def testPullPush(self):
                try:
                        os.system('hg init %s' % SCM_DIR)
                        hgcmd = s.HGCmd()
                        os.system('echo 42 > %s/test' % SCM_DIR)
                        hgcmd.add(SCM_DIR, SCM_DIR + '/test')
                        hgcmd.commit(SCM_DIR, message='adding_test')
                        hgcmd.tag(SCM_DIR, '0', 'test_tag')
                        hgcmd.tag(SCM_DIR, '0', 'test_tag2', 'titi')
                        os.system('echo 43 > %s/test' % SCM_DIR)
                        hgcmd.commit(SCM_DIR, message='modify_test')
                except XUtilsError,e:
                        self.fail(str(e) + '\n' + e.get_error_log())
                
                try:
                        os.system('hg init %s' % SCM_DIR2)
                        hgcmd.pull(SCM_DIR2, 'tip', SCM_DIR)
                        self.failUnlessEqual(hgcmd.tags(SCM_DIR2).keys(), ['test_tag2', 'tip', 'test_tag'])
                        hgcmd.update(SCM_DIR2)
                        os.system('echo 44 > %s/test' % SCM_DIR2)
                        hgcmd.commit(SCM_DIR2, message='modify_test2')
                        hgcmd.tag(SCM_DIR2, 'tip', 'scm2_tag')
                        hgcmd.push(SCM_DIR2, dest=SCM_DIR)

                        hgcmd.update(SCM_DIR)
                        self.failUnless('scm2_tag' in hgcmd.tags(SCM_DIR))
                except XUtilsError,e:
                        self.fail(str(e) + '\n' + e.get_error_log())
                # Test pull/push

        def tearDown(self):
                os.system('rm -rf %s' % SCM_DIR)
                os.system('rm -rf %s' % SCM_DIR2)

if __name__ == "__main__":
        unittest.main()

