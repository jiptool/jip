#! /usr/bin/python
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

import os
import sys
import shutil
import urllib2
import logging
from xml.etree import ElementTree
from string import Template

__author__ = 'Sun Ning <classicning@gmail.com>'
__version__ = '0.1dev'
__license__ = 'GPL'

JYTHON_HOME = os.environ('JYTHON_HOME')
DEFAULT_JAVA_LIB_PATH = JYTHON_HOME+'/javalib'
MAVEN_LOCAL_REPOS = ('local', os.environ['HOME']+'/.m2/repository', 'file')
MAVEN_PUBLIC_REPOS = ('public', "http://repo1.maven.org/maven2/", 'remote')

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

    def __eq__(self, other):
        if isinstance(other, Artifact):
            return other.group == self.group and other.artifact == self.artifact and other.version == self.version
        else:
            return False

    def __str__(self):
        return "%s:%s:%s" % (self.group, self.artifact, self.version)

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


def _get_runtime_dependencies(pom_string):
    eletree = ElementTree.fromstring(pom_string)
    
    dependency_management_version_dict = {}

    dependencyManagement = eletree.findall("dependencyManagement/dependencies/dependency")
    for dependency in dependencies:
        group_id = dependency.findtext("groupId")
        artifact_id = dependency.findtext("artifactId")
        version = dependency.findtext("version")
        dependency_management_version_dict[(group_id, artifact_id)] = version
    ## TODO resolve maven scope "import"

    runtime_dependencies = []
    dependencies = eletree.findall("dependencies/dependency")
    for dependency in dependencies:
        group_id = dependency.findtext("groupId")
        artifact_id = dependency.findtext("artifactId")
        version = dependency.findtext("version")
        scope = dependency.findtext("scope")
        
        # runtime dependency
        if scope is None or scope == 'compile' or scope == 'runtime':
            if version is None:
                version = dependency_management_version_dict[(group_id, artifact_id)]
            artifact = Artifact(group_id, artifact_id, version)
            runtime_dependencies.append(artifact)

    return runtime_dependencies

def _create_repos(name, uri, repos_type):
    if repos_type == 'local':
        return MavenFileSystemRepos(name, uri)
    if repos_type == 'remote':
        return MavenHttpRemoteRepos(name, uri)

MAVEN_REPOS = map(lambda x: _create_repos(*x), [MAVEN_LOCAL_REPOS, MAVEN_PUBLIC_REPOS])

def install(group, artifact, version):
    global MAVEN_REPOS    
    artifact_to_install = Artifact(group, artifact, version)

    dependency_set = set()
    installed_set = set()

    dependency_set.add(artifact_to_install)

    while len(dependency_set) > 0:
        artifact = dependency_set.pop()
        if artifact in installed_set:
            continue

        found = False
        for repos in MAVEN_REPOS:

            pom = repos.download_pom(artifact)

            ## find the artifact
            if pom is not None:
                repos.download_jar(artifact)
                install_set.add(artifact)
                found = True

                more_dependencies = _get_runtime_dependencies(pom)
                for d in more_dependencies: dependency_set.add(d)
                break
        
        if not found:
            logger.error("Artifact not found in repositories: %s", artifact)
            sys.exit(1)

def parse_cmd(args):
    if len(args > 0):
        cmd = args[0]
        values = args[1:]
        return (cmd, values)
    else:
        return None

def main():
    args = sys.argv[1:] 
    cmd, values = parse_cmd(args)
    if cmd == 'install':
        #group, artifact, version = values.split(':')
        install(*values.split(':'))

if __name__ == "__main__":
    main()
