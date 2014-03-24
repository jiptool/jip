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

import os
import sys
import pickle
import threading
from string import Template

from jip import logger
from jip.util import get_virtual_home, get_lib_path

class IndexManager(object):
    """An IndexManager persists the artifacts you installed in your path and 
    keep it consistent"""
    def __init__(self, filepath):
        self.filepath  = filepath
        self.installed = set()
        self.committed = False
        self.persist_lock = threading.Lock()

    def add_artifact(self, artifact):
        self.installed.add(artifact)
        #self.persist()
        
    def get_artifact(self, artifact_eq):
        for artifact in self.installed:
            if artifact == artifact_eq:
                return artifact
        return None

    def remove_artifact(self, artifact):
        a = self.get_artifact(artifact)
        if a is not None:
            self.installed.remove(a)

    def remove_all(self):
        self.installed = set()

    def is_installed(self, artifact_test):
        return self.get_artifact(artifact_test) is not None

    def is_same_installed(self, artifact):
        is_same = lambda a: a.is_same_artifact(artifact)
        return any(map(is_same, self.installed))

    def persist(self):
        if not self.committed:
            return 
        try:
            self.persist_lock.acquire()

            picklefile = open(self.filepath, 'wb')
            pickle.dump(self.installed, picklefile)
            picklefile.close()
        finally:
            self.persist_lock.release()

    def initialize(self):
        self.committed = False
        if os.path.exists(self.filepath):
#            try:
#                pickledata = open(self.filepath, 'rb').read()
#                artifacts = pickle.loads(pickledata)
#                for artifact in artifacts: self.installed.add(artifact)
#                self.keep_consistent()
#            except:
#                pass
             pickledata = open(self.filepath, 'rb').read()
             artifacts = pickle.loads(pickledata)
             for artifact in artifacts: self.installed.add(artifact)
             self.keep_consistent()

    def keep_consistent(self):
        in_path_libs = os.listdir(get_lib_path())
        remembered_libs = list(self.installed)
        for artifact in remembered_libs:
            local_name = artifact.to_jip_name()
            if local_name not in in_path_libs:
                logger.warn(('[Warning] %s is not in your path which should be installed by previous actions. '
                    + 'If you still need it, please reinstall it by: jip install %s') % (local_name, str(artifact)))
                self.remove_artifact(artifact)

    def finalize(self):
        self.persist()

    def commit(self):
        self.committed = True

    def to_pom(self):
        pom_template = Template("""
        <dependency>
            <groupId>$groupId</groupId>
            <artifactId>$artifactId</artifactId>
            <version>$version</version>
        </dependency>""")
        deps = []
        for artifact in self.installed:
            content = pom_template.substitute({'groupId': artifact.group,
                'artifactId': artifact.artifact, 'version': artifact.version}) 
            deps.append(content)

        return ''.join(deps)

index_manager = IndexManager(os.path.join(get_virtual_home(), '.jip_index'))

