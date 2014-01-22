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
import tempfile
import shutil
import subprocess

from os.path import realpath, dirname

curr_path = realpath(dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xutils.ebuild.ebuild_scm as b
from xutils.xerror import XUtilsError

CURR_EBUILD = curr_path + '/ebuilds/base-targets/wms-sdk/wms-sdk-1.4.0.0.ebuild'
CURR_EBUILD2 = curr_path + '/ebuilds/base-targets/wms-sdk/wms-sdk-1.4.0.1.ebuild'
GIT_EBUILD = curr_path + '/ebuilds/adk-1.0.ebuild'


tested_modules=[ 'xutils.ebuild' ]

class ebuildTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = realpath(dirname(sys.modules[__name__].__file__))

        def testEbuildType(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                self.failUnless(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.failUnlessEqual(eb.get_type(), 'target')

        def testEbuildTypeTarget(self):
                eb = b.ebuild_factory(CURR_EBUILD2)
                self.failUnless(eb != None, 'Ebuild not detected as an SCM ebuild')
                self.failUnlessEqual(eb.get_type(), 'target')

        def testEbuildName(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                self.failUnlessEqual(eb.get_name(), 'wms-sdk-1.4.0.0')

        def testEbuildGetVersion(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                self.failUnlessEqual(eb.get_version(), ('1.4.0', {'wms': '1.4.0', 'sdk': 'default'}))

        def testEbuildSetVersion(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                eb.set_version(('4bd81f72f29a', { 'wms' : '2375b3a9c048', 'sdk' : 'f6af2724de14' }))
                self.failUnlessEqual(eb.get_name(), 'wms-sdk-1.4.0.9034.2.23')

        def testEbuildSetVersionPartial(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                eb.set_version(('4bd81f72f29a', None), partial=True)
                self.failUnlessEqual(eb.get_name(), 'wms-sdk-1.4.0.0.0.23')
                del eb
                eb = b.ebuild_factory(CURR_EBUILD)
                eb.set_version((None, None), partial=True)
                del eb
                eb = b.ebuild_factory(CURR_EBUILD)
                eb.set_version((None, { 'wms' : '2375b3a9c048' }))
                self.failUnless(re.match(r'wms-sdk-1\.4\.0\.9034\.[0-9]+\.[0-9]+', eb.get_name()),
                                'bad ebuild bump ebuild_name = %s should be wms-sdk-1.4.0.9034.X.X' % eb.get_name())

        def testEbuildSetVersionBranchCheck(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                try:
                        eb.set_version(('4bd81f72f29a', None), check=True)
                        self.fail('An error should have been raised 1')
                except XUtilsError:
                        pass
                # TODO check branch mismatch with overlays

	def testEbuildUserName(self):
                eb = b.ebuild_factory(CURR_EBUILD)
                eb.set_version(('4bd81f72f29a', None), partial=True, name='user:1.6.1.178')
		self.assertEqual(eb.get_name(), 'wms-sdk-1.6.1.178')

        def _run_cmd(self, *args):
            process = subprocess.Popen(args,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            stdout, stderr = process.communicate()
            exitcode = process.wait()
            if exitcode:
                cmdstr = ' '.join(args)
                raise Exception("Command %s failed with exit code %s" % (cmdstr, exitcode))
            return stdout

        def testSetVersionOnGitOverlay(self):
                oldcwd = os.getcwd()
                tmpdir = tempfile.mkdtemp()
                try:
                    ebuild = os.path.join(tmpdir, 'adk-1.0.ebuild')
                    gitdir = os.path.join(tmpdir, 'git')
                    os.mkdir(gitdir)

                    file = open(ebuild, 'w')
                    file.write("""
inherit target xov mercurial

DESCRIPTION="Test Git overlay"
EAPI="1"
LICENSE="Wyplay"
SLOT="0"

EHG_REPO_URI="genbox/profiles/product/ADK"
EHG_BRANCH="default"

XOV_TEST_PROTO="git"
XOV_TEST_URI="file://%s"
XOV_TEST_REVISION=""
XOV_TEST_BRANCH="master"
XOV_TEST_PORTDIR="True"
""" % gitdir)
                    file.close()

                    os.chdir(gitdir)
                    self._run_cmd('git', 'init')

                    testfile = 'abc'
                    file = open(testfile, 'wb')
                    file.write('abc')
                    file.close()
                    self._run_cmd('git', 'add', testfile)
                    self._run_cmd('git', 'commit', '-a', '-m', 'add file')
                    HEAD = self._run_cmd('git', 'rev-parse', 'HEAD')
                    HEAD = HEAD.rstrip()
                    eb = b.ebuild_factory(ebuild)
                    eb.set_version(('b8e7dea6fb19', {}))

                    git_overlay = eb.ident['overlays'][0]
                    self.assertEqual(git_overlay['name'], 'test')
                    self.assertEqual(git_overlay['branch'], 'master')
                    self.assertEqual(git_overlay['hash'], HEAD)
                    self.assertEqual(git_overlay['proto'], 'git')

                    self.assertEqual(eb.pv['number'], ['1', HEAD[:7], '1152'])
                finally:
                    os.chdir(oldcwd)
                    shutil.rmtree(tmpdir)

        def testGitRepo(self):
                oldcwd = os.getcwd()
                tmpdir = tempfile.mkdtemp()
                try:
                    os.environ['EGIT_BASE_URI'] = 'ssh://git@s1lxblackduck01.wyplay.int'
                    ebuild = os.path.join(tmpdir, 'adk-1.0.ebuild')
                    gitdir = os.path.join(tmpdir, 'git')
                    os.mkdir(gitdir)

                    file = open(ebuild, 'w')
                    file.write("""
inherit target xov git

DESCRIPTION="Test Git overlay"
EAPI="1"
LICENSE="Wyplay"
SLOT="0"

EGIT_REPO_URI="odole/frog-profile.git"
EGIT_BRANCH="master"

XOV_LOCAL_PROTO="git"
XOV_LOCAL_URI="file://%s"
XOV_LOCAL_REVISION=""
XOV_LOCAL_BRANCH="master"
XOV_LOCAL_PORTDIR="True"
""" % gitdir)
                    file.close()

                    os.chdir(gitdir)
                    self._run_cmd('git', 'init')

                    readme = 'README'
                    file = open(readme, 'wb')
                    file.write('abc')
                    file.close()
                    self._run_cmd('git', 'add', readme)
                    self._run_cmd('git', 'commit', '-a', '-m', 'initial import')
                    HEAD = self._run_cmd('git', 'rev-parse', 'HEAD')
                    HEAD = HEAD.rstrip()

                    eb = b.ebuild_factory(ebuild)
		    eb.set_version(('1.0.0', { 'test' : 'HEAD', 'other' : '156'}))
		    self.failUnlessEqual(eb.get_name(), 'adk-1.0.%s.0' % HEAD[0:7])
                finally:
                    os.chdir(oldcwd)
                    shutil.rmtree(tmpdir)


if __name__ == "__main__":
        unittest.main()

