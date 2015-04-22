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

from jip import logger, repos_manager
from jip.commands import resolve as jip_resolve, command
from jip.commands import _install as jip_install
from jip.maven import Artifact
from jip.util import pool

try:
    from setuptools import setup as _setup
    from setuptools.command.install import install as _install
except:    
    from distutils.core import setup as _setup
    from distutils.command.install import install as _install
from distutils.core import Command as _Command    

dist_pom = 'pom.xml'
dependencies = []
repositories = []
exclusions = []
use_pom = True

def requires_java(requires_info):
    global use_pom, dependencies, repositories, exclusions
    use_pom = False
    if 'repositories' in requires_info:
        repositories = requires_info['repositories']
    if 'dependencies' in requires_info:
        dependencies = [Artifact(*d) for d in requires_info['dependencies']]
    if 'exclusions' in requires_info:
        exclusions = [Artifact(*d) for d in requires_info['exclusions']]

@command(register=False)
def requires_java_install():
    for repos in repositories:
        repos_manager.add_repos(repos[0], repos[1], 'remote')
    jip_install(dependencies, exclusions)
    pool.join()
    logger.info("[Finished] all dependencies resolved")

class install(_install):
    def run(self):
        _install.run(self)
        logger.info('running jip_resolve')
        self.run_command('resolve')

class resolve(_Command):
    user_options = []

    def initialize_options(self):
        self.pom_file = dist_pom

    def finalize_options(self):
        pass

    def run(self):
        if use_pom:
            jip_resolve(self.pom_file)
        else:
            requires_java_install()

def setup(**kwargs):
    if 'requires_java' in kwargs:
        requires_java(kwargs.pop('requires_java'))

    if 'pom' in kwargs:
        dist_pom = kwargs.pop('pom')

    if 'cmdclass' not in kwargs:
        kwargs['cmdclass'] = {}

    if 'install' not in kwargs['cmdclass']:
        ## add install command if user doesn't define custom one
        kwargs['cmdclass']['install'] = install
    if 'resolve' not in kwargs['cmdclass']:
        ## add resolve command        
        kwargs['cmdclass']['resolve'] = resolve

    return _setup(**kwargs)

