#! /usr/bin/python
# Copyright (C) <year>  <name of author>

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

import os
import sys
import shutil
import urllib2
import logging
from string import Template

JYTHON_HOME = os.environ('JYTHON_HOME')
DEFAULT_JAVA_LIB_PATH = JYTHON_HOME+'/javalib'
MAVEN_LOCAL_REPOS = ('local', os.environ['HOME']+'/.m2/repository', 'file')
MAVEN_PUBLIC_REPOS = ('public', "http://repo1.maven.org/maven2/", 'http')

MAVEN_REPOS = [MAVEN_LOCAL_REPOS, MAVEN_PUBLIC_REPOS]

logger = logging.logger()

class Artifact(object):
    def __init__(self, group, artifact, version):
        self.group = group
        self.artifact = artifact
        self.version = version

    def to_jip_name(self, pattern="$artifact-$version.$ext", ext="jar"):
        template = Template(pattern)
        filename = template.substitute({'group':self.group, 'artifact':self.artifact, 
                'version': self.version, 'ext': self.ext})
        return filename

    def to_maven_name(self, ext):
        group = self.group.replace('.', '/')
        return "%s/%s/%s/%s-%s.%s" % (group, self.artifact, self.version, self.artifact, self.version, ext)

class MavenRepos(object):
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri

    def get_artifact_uri(self, artifact, ext):
        pass

    def download_jar(self, artifact, local_path=DEFAULT_JAVA_LIB_PATH):
        """ download or copy file to local path, raise exception when failed """
        pass

    def download_pom(self, artifact):
        """ return a content string """
        pass
        
class MavenFileSystemRepos(MavenRepos):
    def __init__(self, name, uri):
        MavenRepos.__init__(self, name, uri)

    def get_artifact_uri(self, artifact, ext)
        maven_name = artifact.to_maven_name(ext)
        maven_file_path = self.uri + maven_name
        return maven_file_path

    def download_jar(self, artifact, local_path=DEFAULT_JAVA_LIB_PATH):
        maven_file_path = self.get_artifact_uri(artifact, 'jar')
        logger.info("Retrieving jar package from %s:" % self.name)
        logger.info("%s" % maven_file_path)
        if os.path.exsits(maven_file_path):
            local_jip_path = local_path+"/"+artifact.to_jip_name()
            shutil.copy(maven_file_path, local_jip_path)
        else:
            raise IOError('File not found:' + maven_file_path)

    def download_pom(self, artifact):
        maven_file_path = self.get_artifact_uri(artifact, 'pom')
        if os.path.exsits(maven_file_path):
            pom_file = open(maven_file_path, 'r')
            data =  pom_file.read()
            pom_file.close()
            return data
        else:
            return None

class MavenHttpRemoteRepos(MavenRepos):
    def __init__(self, name, uri):
        MavenRepos.__init__(self, name, uri)

    def download_jar(self, artifact, local_path=DEFAULT_JAVA_LIB_PATH):
        maven_path = self.get_artifact_uri(artifact, 'jar')
        f = urllib2.urlopen(maven_path)
        data =  f.open()
        f.close()

        local_jip_path = local_path+"/"+artifact.to_jip_name()
        local_f = open(local_jip_path, 'w')
        local_f.write(data)
        local_f.close()

    def download_pom(self, artifact):
        maven_path = self.get_artifact_uri(artifact, 'pom')
        try:
            f = urllib2.urlopen(maven_path)
            data =  f.open()
            f.close()
            return data
        except urllib2.HTTPError:
            return None

    def get_artifact_uri(self, artifact, ext)
        maven_name = artifact.to_maven_name(ext)
        maven_path = self.uri + maven_name
        return maven_path



