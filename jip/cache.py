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

from repository import MavenRepos

import os
import shutil

class CacheRepository(MavenRepos):
    def __init__(self):
        self.name = 'cache'
        self.uri = os.path.expanduser('~/.jip/cache')
        if not os.path.exists(self.uri):
            os.makedirs(self.uri)

    def get_artifact_uri(self, artifact, ext):
        group = artifact.group
        name = artifact.artifact+"-"+artifact.version+"."+ext

        return os.path.join(self.uri, group, 
                artifact.artifact, name)

    def download_jar(self, artifact, local_path=None):
        path = self.get_artifact_uri(artifact, 'jar')
        shutil.copy(path, local_path)
        
    def download_pom(self, artifact):
        path = self.get_artifact_uri(artifact, 'pom')
        if os.path.exists(path):
            f = open(path, 'r')
            data = f.read()
            f.close()
            return data
        else:
            return None

    def put_pom(self, artifact, data):
        path = self.get_artifact_uri(artifact, 'pom')
        f = open(path, 'w')
        f.write(data)
        f.close()

    def put_jar(self, artifact, jarpath):
        path = self.get_artifact_uri(artifact, 'jar')
        shutil.copy(jarpath, path)

class CacheManager(object):
    def __init__(self, enable):
        self.enable = enable
        self.cache = CacheRepository()

    def get_artifact_pom(self, artifact):
        if self.enable:
            return self.cache.download_pom(artifact)
        else:
            return None

    def get_artifact_jar(self, artifact, topath):
        if self.enable:
            self.cache.download_jar(artifact, topath)

    def put_artifact_pom(self, artifact, data):
        self.cache.put_pom(artifact, data)

    def put_artifact_jar(self, artifact, jarpath):
        self.cache.put_jar(artifact, jarpath)

cache_manager = CacheManager()

