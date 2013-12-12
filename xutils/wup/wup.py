#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import exceptions, struct

class wupError(exceptions.Exception):
        def __init__(self, msg):
                self.msg = msg
        def __str__(self):
                return self.msg

class wupParser(object):
        def __init__(self, file):
                self.file = file
                self.sections = None 
        
        def parse(self):
                self.sections = {}
                fd = open(self.file, 'rb')
                buff = fd.read(3)
                if buff != 'WPD':
                        fd.close()
                        raise wupError("Wrong file format")
                while self.__parse_section(fd):
                        pass
                fd.close()

        def __parse_section(self, fd):
                buff = fd.read(2)
                if not buff:
                        return False
                len = struct.unpack('>H', buff)[0]
                section = fd.read(len)
                len = struct.unpack('>I', fd.read(4))[0]
                self.sections[section] = [ fd.tell(), len ]
                fd.seek(len, 1)
                return True

        def get_section(self, name):
                if not self.sections:
                        self.parse()

                section = self.sections.get(name, None)
                if not section:
                        return (None, -1)

                fd = open(self.file, 'rb')
                fd.seek(section[0])
                return (fd, section[1])

        def copy_section(self, name, file, length=16*1024):
                fdsrc, size = self.get_section(name)

                if not fdsrc or size <= 0:
                        return False
                fddst = open(file, 'wb')

                while 1:
                        len = min(size, length)
                        size -= len
                        buf = fdsrc.read(len)
                        if not buf:
                                break
                        fddst.write(buf)
                fddst.close()
                fdsrc.close()
                return True

