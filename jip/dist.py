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

from jip.commands import resolve

try:
    from setuptools import setup as _setup
    from setuptools.command.install import install as _install
except:    
    from distutils.core import setup as _setup
    from distutils.command.install import install as _install

dist_descriptor = 'pom.xml'
class install(_install):
    def run(self):
        _install.run(self)
        print 'running jip.resolve'
        resolve(dist_descriptor)

def setup(**kwargs):
    if 'cmdclass' not in kwargs:
        kwargs['cmdclass'] = {'install': install}
    _setup(**kwargs)

