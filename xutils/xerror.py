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

