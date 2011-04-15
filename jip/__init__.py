#! /usr/bin/env jython
# Copyright (C) 2011 Sun Ning<classicning@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

JIP_VERSION = '0.4'
__author__ = 'Sun Ning <classicning@gmail.com>'
__version__ = JIP_VERSION
__license__ = 'MIT'

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

