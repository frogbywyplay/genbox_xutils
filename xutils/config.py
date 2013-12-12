#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
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

