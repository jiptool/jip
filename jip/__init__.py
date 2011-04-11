#! /usr/bin/env jython
# Copyright (C) 2011 Sun Ning<classicning@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
JIP_VERSION = '0.4dev'
__author__ = 'Sun Ning <classicning@gmail.com>'
__version__ = JIP_VERSION
__license__ = 'GPL'

import os
import sys
import logging
logging.basicConfig(level=logging.INFO, format="\033[1m%(name)s\033[0m  %(message)s")
logger = logging.getLogger('jip')

def get_virtual_home():
    if 'VIRTUAL_ENV' in os.environ:
        JYTHON_HOME = os.environ['VIRTUAL_ENV']
    else:
        logger.warn('Warning: no virtualenv detected, remember to activate it.')
        if 'JYTHON_HOME' in os.environ:
            JYTHON_HOME = os.environ['JYTHON_HOME']
        else:
            ## fail back to use current directory
            JYTHON_HOME = os.getcwd()
    return JYTHON_HOME            

def get_lib_path():
    JYTHON_HOME = get_virtual_home()        
    DEFAULT_JAVA_LIB_PATH = os.path.join(JYTHON_HOME, 'javalib')

    if not os.path.exists(DEFAULT_JAVA_LIB_PATH):
        os.mkdir(DEFAULT_JAVA_LIB_PATH)
    return DEFAULT_JAVA_LIB_PATH        

