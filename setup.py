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

from distutils.core import setup

setup(
    name="jip",
    version="0.2dev3",
    author="Sun Ning",
    author_email="classicning@gmail.com",
    url="https://github.com/sunng87/jip",
    description="jip installs packages, for Jython",
    scripts = ["scripts/jip", "scripts/jython-all"],
    license='gpl',
    py_modules=['jip'],
    long_description="""
    Due to the complexity of traditional Java dependency management tool(ivy/maven), I created jip for simple and easy, in a pythonic way. Use jip, you can download and install jars from maven central repositories, just like the way of well known python package management tool, pip.

The typical usage of jip is:
jip install [groupId]:[artifactId]:[version]
Currently, jip must be used within virtualenv, this is also a best practice for you to create and manage portable environments of python.

jip is under active development, and does not have a stable release currently.
    """,
    classifiers=['Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Java',
        'Environment :: Console',
        'Operating System :: POSIX']
)


