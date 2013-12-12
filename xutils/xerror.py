#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

from exceptions import Exception

class XUtilsError(Exception):
        """ Generic error class for XUtils. """
        def __init__(self, error, num=None, error_log=None):
                if error_log:
                        self.error_log = error_log.strip(" \t\n")
                else:
                        self.error_log = None

                self.error = error.strip(" \t\n")
                self.num = num

        def get_error(self):
                return self.error

        def get_error_log(self):
                return self.error_log

        def get_error_number(self):
                if self.num is None:
                        return 0
                else:
                        return self.num

        def __str__(self):
                return self.get_error()

        def __int__(self):
                return self.get_error_number()

