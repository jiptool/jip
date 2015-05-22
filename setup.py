# Copyright (C) 2011-2015 Sun Ning<classicning@gmail.com>
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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from jip import JIP_VERSION as version

long_description = open('README.rst').read()

def is_virtualenv():
    import os
    return 'VIRTUAL_ENV' in os.environ

setup_args=dict(
        name="jip",
        version=version,
        author="Sun Ning",
        author_email="classicning@gmail.com",
        url="https://github.com/sunng87/jip",
        description="jip installs packages, for Jython and Python",
        license='mit',
        packages=['jip'],
        long_description=long_description,
        classifiers=['Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Topic :: Software Development :: Build Tools',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Java',
            'Environment :: Console',
            'Operating System :: POSIX']
)

setup_args['scripts'] = ["scripts/jython-all"]
requires = ['requests']
if sys.version_info < (2, 7):
    requires.append('argparse')
setup_args['install_requires'] = requires
setup_args['entry_points'] = {
            'console_scripts' : [
                'jip = jip.main:main'
            ]
        }
setup_args['data_files'] = [('data', ['data/pom.tpl'])]

setup(**setup_args)

