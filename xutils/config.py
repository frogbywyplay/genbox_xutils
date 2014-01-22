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

from ConfigParser import SafeConfigParser

class XUtilsConfig(object):
	def __init__(self, config_files):
		self.parser = SafeConfigParser()
                self.config_files = config_files

                if type(config_files) is str:
                        self.parser.read(self.config_files)
                elif type(config_files) is list:
                        for cfg in config_files:
                		self.parser.read(cfg)

	def get(self, section, option, default=None, env_key=None, env=None):
		"""
		Retrieve element's value from configuration.
		An element is defined by a couple section/option
		Value coming from configuration can be overwritten by environ.

		section: section of the configuration elements 
		option: option of the configuration elements
		env_key: element corresponding environment variable
		env: environment to use
		If env is None, os.environ is used.		
		"""
		value = default
		if self.parser.has_option(section, option):
			value = self.parser.get(section, option)
		if env_key:
			if not env:
				from os import environ
				env = environ.copy()
			if env.has_key(env_key):
				value = env[env_key]
		return value

        def getboolean(self, section, option, default=False):
                value = default
                if self.parser.has_option(section, option):
                        try:
                                value = self.parser.getboolean(section, option)
                        except ValueError, e:
                                value = default
                return value

