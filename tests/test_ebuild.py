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
import xutils.ebuild as b
from xutils.xerror import XUtilsError

EBUILD_TMP= curr_path + '/ebuilds/sys-apps/xutils/'
EB1 = 'xutils-1.0.0.0-r1.ebuild'


tested_modules=[ 'xutils.ebuild' ]
class ebuildTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def testEbuildErrors(self):
                self.error = 1
                try:
                        b.XEbuild(None)
                except XUtilsError, e:
                        self.error = 0
                self.failUnlessEqual(self.error, 0, 'An error should have been raised')
                self.error = 1
                try:
                        b.XEbuild('test.pouet')
                except XUtilsError, e:
                        self.error = 0
                self.failUnlessEqual(self.error, 0, 'An error should have been raised')
                self.error = 1
                try:
                        b.XEbuild('test.ebuild')
                except XUtilsError, e:
                        self.error = 0
                self.failUnlessEqual(self.error, 0, 'An error should have been raised')

        def testEbuildExpand(self):
                eb = b.XEbuild(EBUILD_TMP + EB1)
                self.failUnlessEqual(eb.expand_vars('PN=$PN/PV=$PV/P=$P/PR=$PR/PVR=$PVR/PF=${PF}/CAT=${CATEGORY}'),
                        'PN=xutils/PV=1.0.0.0/P=xutils-1.0.0.0/PR=r1/PVR=1.0.0.0-r1/PF=xutils-1.0.0.0-r1/CAT=sys-apps')

        def testEbuildNoExpand(self):
                eb = b.XEbuild(EBUILD_TMP + EB1)
                self.failUnlessEqual(eb.expand_vars(r'\$$ \${TEST}'), r'\$$ \${TEST}')
                self.failUnlessEqual(eb.expand_vars(r'$ ${TEST}'), r'$ ')

        def testEbuildExpandError(self):
                eb = b.XEbuild(EBUILD_TMP + EB1)
                eb._read_file()
                try:
                        print eb.expand_vars(r'${{{TEST}}')
                except XUtilsError:
                        return
                self.fail('An error should have been raised')

        def testEbuildGetVar(self):
                eb = b.XEbuild(EBUILD_TMP + EB1)
                try:
                        eb.get_var('EHG_REPO_URI')
                        self.fail('An error should have been raised')
                except XUtilsError:
                        pass
                eb._read_file()
                self.failUnlessEqual(eb.get_var('EHG_REPO_URI'), 'genbox/genbox-tools/xutils')
                self.failUnlessEqual(eb.get_var('EHG_R.?PO_URI', dict=True), {'var' : 'EHG_REPO_URI', 'value' : 'genbox/genbox-tools/xutils'})
                self.failUnlessEqual(eb.get_var('EHG_.*', dict=True, all=True), [{ 'var' : 'EHG_REPO_URI', 'value' : 'genbox/genbox-tools/xutils' },
                                                                                 { 'var' : 'EHG_BRANCH', 'value' : 'default' }])
                self.failUnlessEqual(eb.get_var('EHG_.*', dict=False, all=True), ['genbox/genbox-tools/xutils', 'default'])

        def testGetCPV(self):
                eb = b.XEbuild(EBUILD_TMP + EB1)
                self.failUnlessEqual(eb.get_cpv(), 'sys-apps/xutils-1.0.0.0-r1')

if __name__ == "__main__":
        unittest.main()

