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

import sys

from . import logger
from jip.commands import commands

def parse_cmd(argus):
    if len(argus) > 0:
        cmd = argus[0]
        values = argus[1:]
        return (cmd, values)
    else:
        return (None, None)

def print_help():
    print "Available commands:"
    for name, func in commands.items():
        print "\t%s\t\t%s" % (name, func.__doc__)

def main():
    logger.debug("sys args %s" % sys.argv)
    args = sys.argv[1:] 
    cmd, values = parse_cmd(args)
    if cmd in commands:
        commands[cmd](*values)
    else:
        print_help()
        
