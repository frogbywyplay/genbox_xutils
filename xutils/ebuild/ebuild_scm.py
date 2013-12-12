#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import re
from ebuild import ebuild_match, XEbuild

class XEbuildSCMFactory(object):
        def __init__(self):
                self.__db = []
        def register(self, ebuild_class):
                self.__db.insert(0, ebuild_class)
        def __call__(self, file):
                fdin = open(file, "r")
                file_buffer = fdin.readlines()
                fdin.close()

                for cl in self.__db:
                        if cl.check_type(file_buffer):
                                return cl(name=file, buffer=file_buffer)
                return None

ebuild_factory = XEbuildSCMFactory()

re_tag_name = re.compile(r'^\d+(\.\d+)*[a-z]?$')

class XEbuildSCM(XEbuild):
        def __init__(self, name, buffer=None):
                XEbuild.__init__(self, name, buffer)
                if not self.buffer:
                        self._read_file(name)

        def get_branch(self):
                return None
        def get_version(self):
		""" Returns the SCM version of this ebuild
			(defaults to branch if this is a HEAD ebuild) """
                return None
        def set_version(self, version, check=False, name='shortrev'):
                """ 
                        @param version, the version to set
                        @param check, make some integrity check about the version (check the branch information in the ebuild)
                        @param name, the method tu use to rename the ebuild, can be 'shortrev' or 'tag'
                """
                pass
        def get_uri(self):
                return None
        def get_type(self):
                return 'undefined'
        def get_latest(self):
                return None

        def is_template(self):
                return False

