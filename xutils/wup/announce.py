#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import exceptions
import xml.etree.ElementTree as etree

class announceError(exceptions.Exception):
        def __init__(self, msg):
                self.msg = msg
        def __str__(self):
                return self.msg

class announceParser(object):
        def __init__(self, file=None):
                self.file = file
                self.tree = self.__load()

        def __load(self):
                if type(self.file) == str:
                        fd = open(self.file, 'r')
                else:
                        fd = self.file
                self.tree = etree.parse(fd)
                fd.close()
                self.root = self.tree.getroot()

        def get_text(self, name):
                res = []
                for node in self.root.findall(name):
                        res.append(node.text)
                return res

        def get_targets(self):
                targets = self.get_text('./update/target')
                targets += self.get_text('./update/targetList/target')
                return targets

        def get_version(self):
                version = self.get_text('./update/version')
                if len(version) != 1:   
                        raise announceError('version error')
                return version[0]

