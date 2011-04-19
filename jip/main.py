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


import sys

from . import logger
from .commands import commands

def parse_cmd(argus):
    if len(argus) > 0:
        cmd = argus[0]
        values = argus[1:]
        return (cmd, values)
    else:
        return (None, None)

def print_help():
    print "jip install packages, for jython\n"
    print "Available commands:"
    for name, func in commands.items():
        print "  %-10s%s" % (name, func.__doc__)

def main():
    logger.debug("sys args %s" % sys.argv)
    args = sys.argv[1:] 
    cmd, values = parse_cmd(args)
    if cmd in commands:
        commands[cmd](*values)
    else:
        print_help()
        
