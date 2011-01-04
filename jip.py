#! ./bin/jython
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
import re
from xml.etree import ElementTree
from string import Template

__author__ = 'Sun Ning <classicning@gmail.com>'
__version__ = '0.1dev'
__license__ = 'GPL'

JYTHON_HOME = os.environ['VIRTUAL_ENV']
DEFAULT_JAVA_LIB_PATH = JYTHON_HOME+'/javalib'

if not os.path.exists(DEFAULT_JAVA_LIB_PATH):
    os.mkdir(DEFAULT_JAVA_LIB_PATH)

MAVEN_LOCAL_REPOS = ('local', os.environ['HOME']+'/.m2/repository', 'local')
MAVEN_PUBLIC_REPOS = ('public', "http://repo1.maven.org/maven2/", 'remote')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('jip')

class Artifact(object):
    def __init__(self, group, artifact, version):
        self.group = group
        self.artifact = artifact
        self.version = version

    def to_jip_name(self, pattern="$artifact-$version.$ext", ext="jar"):
        template = Template(pattern)
        filename = template.substitute({'group':self.group, 'artifact':self.artifact, 
                'version': self.version, 'ext': ext})
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

    def get_artifact_uri(self, artifact, ext):
        maven_name = artifact.to_maven_name(ext)
        maven_file_path = self.uri + maven_name
        return maven_file_path

    def download_jar(self, artifact, local_path=DEFAULT_JAVA_LIB_PATH):
        maven_file_path = self.get_artifact_uri(artifact, 'jar')
        logger.info("Retrieving jar package from %s:" % self.name)
        logger.info("%s" % maven_file_path)
        if os.path.exsits(maven_file_path):
            local_jip_path = local_path+"/"+artifact.to_jip_name()
            logger.info("Copying file %s" % maven_file_path)
            shutil.copy(maven_file_path, local_jip_path)
            logger.info("Copy file to %s completed" % local_jip_path)
        else:
            raise IOError('File not found:' + maven_file_path)

    def download_pom(self, artifact):
        maven_file_path = self.get_artifact_uri(artifact, 'pom')
        if os.path.exists(maven_file_path):
            logger.info('Opening pom file %s'% maven_file_path)
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
        logger.info('Downloading jar from %s' % maven_path)
        f = urllib2.urlopen(maven_path)
        data =  f.read()
        f.close()

        local_jip_path = local_path+"/"+artifact.to_jip_name()
        local_f = open(local_jip_path, 'w')
        local_f.write(data)
        local_f.close()
        logger.info('Jar download completed to %s' % maven_path)

    def download_pom(self, artifact):
        maven_path = self.get_artifact_uri(artifact, 'pom')
        try:
            logger.info('Opening pom file %s'% maven_path)
            f = urllib2.urlopen(maven_path)
            data =  f.read()
            f.close()
            return data
        except urllib2.HTTPError:
            logger.info('Pom file not found at %s'% maven_path)
            return None

    def get_artifact_uri(self, artifact, ext):
        maven_name = artifact.to_maven_name(ext)
        maven_path = self.uri + maven_name
        return maven_path

def _get_element_from_pom_string(pom_string):
    ## we use this dirty method to remove namesapce attribute so that elementtree will use default empty namespace
    pom_string = re.sub(r"<project(.|\s)*?>", '<project>', pom_string, 1)
    eletree = ElementTree.fromstring(pom_string)
    return eletree

def _get_properties_from_element(eletree):
    # parsing in-pom properties
    properties = {}
    properties_eles = eletree.findall("properties/property")
    for prop in properties_eles:
        name = prop.get("name")
        value = prop.get("value")
        properties[name] = value
    return properties

def _get_in_pom_properties_from_element(eletree):
    properties = {}
    properties["project.groupId"] = eletree.findtext('groupId')
    properties["project.artifactId"] = eletree.findtext('artifactId')
    properties["project.version"] = eletree.findtext('version')

    properties["pom.groupId"] = eletree.findtext('groupId')
    properties["pom.artifactId"] = eletree.findtext('artifactId')
    properties["pom.version"] = eletree.findtext('version')
    return properties

def _replace_placeholder(text, properties):
    def subfunc(matchobj):
        key = matchobj.group(1)
        if key in properties:
            return properties[key]
        else:
            return matchobj.group(0)
    return re.sub(r'\$\{(.*?)\}', subfunc, text)

def _get_dependency_management_from_element(eletree, repos):
    dependency_management_version_dict = {}
    # parsing parent pom for dependencyManagement (allow this method to download another pom from current repository)
    parent = eletree.find("parent")
    if parent is not None:
        parent_group_id = parent.findtext("groupId")
        parent_artifact_id = parent.findtext("artifactId")
        parent_version_id = parent.findtext("version")

        artifact = Artifact(parent_group_id, parent_artifact_id, parent_version_id)
        parent_pom = repos.download_pom(artifact)

        parent_pom_ele = _get_element_from_pom_string(parent_pom)
        
        ## parse parent pom recursively
        parent_dependency_management_dict = _get_dependency_management_from_element(parent_pom_ele, repos)
        dependency_management_version_dict.update(parent_dependency_management_dict)

    properties = _get_properties_from_element(eletree)

    dependency_management_dependencies = eletree.findall("dependencyManagement/dependencies/dependency")
    for dependency in dependency_management_dependencies:
        group_id = _replace_placeholder(dependency.findtext("groupId"), properties)
        artifact_id = _replace_placeholder(dependency.findtext("artifactId"), properties)
        version = _replace_placeholder(dependency.findtext("version"), properties)
        dependency_management_version_dict[(group_id, artifact_id)] = version
    ## TODO resolve maven scope "import"

    return dependency_management_version_dict

def _get_runtime_dependencies(pom_string, repos):
    eletree = _get_element_from_pom_string(pom_string)

    dependency_management_version_dict = _get_dependency_management_from_element(eletree, repos)

    properties = _get_properties_from_element(eletree)

    runtime_dependencies = []
    dependencies = eletree.findall("dependencies/dependency")
    logger.debug('Find dependencies declare: %s'% dependencies)
    for dependency in dependencies:
        # resolve placeholders in pom (properties and pom references)
        group_id = _replace_placeholder(dependency.findtext("groupId"), properties)
        artifact_id = _replace_placeholder(dependency.findtext("artifactId"), properties)
        version = dependency.findtext("version")
        if version is not None:
            version = _replace_placeholder(version, properties)

        scope = dependency.findtext("scope") or ''
        optional = dependency.findtext("optional") or ''

        # runtime dependency
        if (scope == '' or scope == 'compile' or scope == 'runtime') and (optional == '' or optional == 'false'):
            if version is None:
                version = dependency_management_version_dict[(group_id, artifact_id)]
            artifact = Artifact(group_id, artifact_id, version)
            runtime_dependencies.append(artifact)

    logger.debug('Find dependencies: %s'% runtime_dependencies)
    return runtime_dependencies

def _create_repos(name, uri, repos_type):
    if repos_type == 'local':
        return MavenFileSystemRepos(name, uri)
    if repos_type == 'remote':
        return MavenHttpRemoteRepos(name, uri)

## TODO allow custom repository configuration from a config file
MAVEN_REPOS = map(lambda x: _create_repos(*x), [MAVEN_LOCAL_REPOS, MAVEN_PUBLIC_REPOS])

def install(group, artifact, version):
    global MAVEN_REPOS    
    artifact_to_install = Artifact(group, artifact, version)

    ## ready set contains artifact jip file names
    ready_set = os.listdir(DEFAULT_JAVA_LIB_PATH)
    
    ## dependency_set and installed_set contain artifact objects
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
                if not artifact.to_jip_name() in ready_set:
                    repos.download_jar(artifact)
                    installed_set.add(artifact)
                found = True

                more_dependencies = _get_runtime_dependencies(pom, repos)
                for d in more_dependencies: dependency_set.add(d)
                break
        
        if not found:
            logger.error("Artifact not found in repositories: %s", artifact)
            sys.exit(1)

def clean():
    logger.info("remove java libs in %s" % DEFAULT_JAVA_LIB_PATH)
    shutil.rmtree(DEFAULT_JAVA_LIB_PATH)

def parse_cmd(argus):
    if len(argus) > 0:
        cmd = argus[0]
        values = argus[1:]
        return (cmd, values)
    else:
        return None

def main():
    logger.debug("sys args %s" % sys.argv)
    args = sys.argv[1:] 
    cmd, values = parse_cmd(args)
    ## TODO a command dict contains data structure: (command_name, command function )
    if cmd == 'install':
        #group, artifact, version = values.split(':')
        install(*values[0].split(':'))
    elif cmd == 'clean':
        clean()
## TODO another resolve task, allow jip to resovle dependencies from a pom file.
## TODO a paste template to generate a basic structure of jython project (contains a pom file)

if __name__ == "__main__":
    main()
