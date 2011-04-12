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


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from jip import JIP_VERSION as version

setup(
    name="jip",
    version=version,
    author="Sun Ning",
    author_email="classicning@gmail.com",
    url="https://github.com/sunng87/jip",
    description="jip installs packages, for Jython",
    scripts = ["scripts/jip", "scripts/jython-all"],
    license='mit',
    packages=['jip'],
    long_description="""
    Due to the complexity of traditional Java dependency management tool(ivy/maven), I created jip for simple, easy and pythonic. With jip, you can download and install jars from maven central repositories, just like the way of well known python package management tool, pip.

The typical usage of jip is:
jip install [groupId]:[artifactId]:[version]
Currently, jip must be used within virtualenv, this is also a best practice for you to create and manage portable environments of python.

jip is under active development, and does not have a stable release currently.
    """,
    classifiers=['Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Java',
        'Environment :: Console',
        'Operating System :: POSIX']
)


