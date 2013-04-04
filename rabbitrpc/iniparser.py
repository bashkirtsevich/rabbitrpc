# coding=utf-8
#
# $Id: $
#
# NAME:         parser.py
#
# AUTHOR:       Nick Whalen <nickw@mindstorm-networks.net>
# COPYRIGHT:    2013 by Nick Whalen
# LICENSE:
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# DESCRIPTION:
#   Subclasses ConfigParser to produce confg dicts.
#


import ConfigParser

class IniParser(ConfigParser.ConfigParser):
    """
    Subclasses ConfigParser to provide a config dict.

    """
    def as_dict(self):
        config_dict = dict(self._sections)
        for k in config_dict:
            config_dict[k] = dict(self._defaults, **config_dict[k])
            config_dict[k].pop('__name__', None)
        return config_dict
    #---
#---