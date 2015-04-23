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
import argparse

from jip import logger
from jip.commands import commands

def main():
    logger.debug("sys args %s" % sys.argv)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    for name, func in commands.items():
        sb = subparsers.add_parser(name, help=func.__doc__)
        for argspec in func.args:
            name, defaults = argspec
            nargs = None if defaults is None else argparse.OPTIONAL
            sb.add_argument(name, nargs=nargs, type=str)

        for option in func.options:
            name, nargs, description,option_type = option
            if nargs == 0:
                sb.add_argument('--'+name, action='store_true',
                        help=description, dest="options."+name)
            else:
                sb.add_argument('--'+name, nargs=nargs, help=description,
                        type=option_type, dest="options."+name)
    
    args = vars(parser.parse_args())
    cmd = args.pop('command')
    options = {}
    for k in list(args.keys()):
        if k.startswith('options.'):
            v = args.pop(k)
            k = k[k.index('.')+1:]
            options[k] = v

    if options:
        args['options'] = options
    logger.debug(args)
    commands[cmd](**args)

