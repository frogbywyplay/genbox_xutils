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
import xutils.config as c

CFG_TMP= curr_path + '/test.cfg'

class configTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

	def setUp(self):
                cfg = open(CFG_TMP, 'w')
                print >>cfg, '[test1]\n' + \
                        'test = 42\n' + \
                        'titi = 43\n' + \
                        '\n' + \
                        '[bool]\n' + \
                        'billy = True\n' + \
                        'bob = False\n' + \
                        'charly = 2443'
                cfg.close()
		self.env_bkup = os.environ.copy()

	def tearDown(self):
		os.environ = self.env_bkup
		os.unlink(CFG_TMP)
		
        def testConfig(self):
                cfg = c.XUtilsConfig(CFG_TMP)
                self.failUnlessEqual(cfg.get('test1', 'test'), '42')
                self.failUnlessEqual(cfg.get('test1', 'test2'), None)
                self.failUnlessEqual(cfg.get('toto', 'test'), None)
                cfg = c.XUtilsConfig([ '/pouet', CFG_TMP ])
                self.failUnlessEqual(cfg.get('test1', 'test'), '42')
                self.failUnlessEqual(cfg.get('test1', 'test2'), None)
                self.failUnlessEqual(cfg.get('toto', 'test'), None)		
                self.failUnlessEqual(cfg.getboolean('bool', 'billy'), True)
                self.failUnlessEqual(cfg.getboolean('bool', 'billy', False), True)
                self.failUnlessEqual(cfg.getboolean('bool', 'bob'), False)
                self.failUnlessEqual(cfg.getboolean('bool', 'bob', True), False)
                self.failUnlessEqual(cfg.getboolean('bool', 'charly', True), True)
                self.failUnlessEqual(cfg.getboolean('bool', 'charly', False), False)

	def testConfigEnv(self):
		env = {'BILLY': '58'}
		cfg = c.XUtilsConfig(CFG_TMP)
		self.failUnlessEqual(cfg.get('test1', 'test'), '42')
		self.failUnlessEqual(cfg.get('test1', 'test', env_key='BILLY'), '42')
		os.environ['BILLY'] = '64'
		self.failUnlessEqual(cfg.get('test1', 'test', env_key='BOB'), '42')
		self.failUnlessEqual(cfg.get('test1', 'test', env_key='BILLY'), '64')
		self.failUnlessEqual(cfg.get('test1', 'test', env_key='BILLY', env=env), '58')

if __name__ == "__main__":
        unittest.main()

