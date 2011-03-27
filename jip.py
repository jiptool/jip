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
import stat
import locale
import time
import hashlib
from xml.etree import ElementTree
from string import Template
from ConfigParser import ConfigParser

__author__ = 'Sun Ning <classicning@gmail.com>'
__version__ = '0.2dev'
__license__ = 'GPL'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('jip')

## check virtual environ and warn user
if 'VIRTUAL_ENV' in os.environ:
    JYTHON_HOME = os.environ['VIRTUAL_ENV']
else:
    logger.warn('Warning: no virtualenv detected, remember to activate it.')
    if 'JYTHON_HOME' in os.environ:
        JYTHON_HOME = os.environ['JYTHON_HOME']
    else:
        ## fail back to use current directory
        JYTHON_HOME = os.getcwd()
        
DEFAULT_JAVA_LIB_PATH = os.path.join(JYTHON_HOME, 'javalib')

if not os.path.exists(DEFAULT_JAVA_LIB_PATH):
    os.mkdir(DEFAULT_JAVA_LIB_PATH)

MAVEN_LOCAL_REPOS = ('local', os.path.expanduser('~/.m2/repository'), 'local')
MAVEN_PUBLIC_REPOS = ('public', "http://repo1.maven.org/maven2/", 'remote')

class Artifact(object):
    def __init__(self, group, artifact, version):
        self.group = group
        self.artifact = artifact
        self.version = version
        self.timestamp = None
        self.build_number = None

    def to_jip_name(self, pattern="$artifact-$version.$ext", ext="jar"):
        template = Template(pattern)
        filename = template.substitute({'group':self.group, 'artifact':self.artifact, 
                'version': self.version, 'ext': ext})
        return filename

    def to_maven_name(self, ext):
        group = self.group.replace('.', '/')
        return "%s/%s/%s/%s-%s.%s" % (group, self.artifact, self.version, self.artifact, self.version, ext)

    def to_maven_snapshot_name(self, ext):
        group = self.group.replace('.', '/')
        version_wo_snapshot = self.version.replace('-SNAPSHOT', '')
        return "%s/%s/%s/%s-%s-%s-%s.%s" % (group, self.artifact, self.version, self.artifact, version_wo_snapshot,
                self.timestamp, self.build_number, ext)

    def __eq__(self, other):
        if isinstance(other, Artifact):
            return other.group == self.group and other.artifact == self.artifact and other.version == self.version
        else:
            return False

    def __str__(self):
        return "%s:%s:%s" % (self.group, self.artifact, self.version)

    def is_snapshot(self):
        return self.version.find('SNAPSHOT') > 0

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

    def last_modified(self, artifact):
        """ return last modified timestamp """
        pass

    def download_check_sum(self, checksum_type, origin_file_name):
        """ return pre calculated checksum value, only avaiable for remote repos """
        pass
        
class MavenFileSystemRepos(MavenRepos):
    def __init__(self, name, uri):
        MavenRepos.__init__(self, name, uri)

    def get_artifact_uri(self, artifact, ext):
        maven_name = artifact.to_maven_name(ext)
        maven_file_path = os.path.join(self.uri,maven_name)
        return maven_file_path

    def download_jar(self, artifact, local_path=DEFAULT_JAVA_LIB_PATH):
        maven_file_path = self.get_artifact_uri(artifact, 'jar')
        logger.info("Retrieving jar package from %s:" % self.name)
        logger.info("%s" % maven_file_path)
        if os.path.exists(maven_file_path):
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
            logger.info('Pom file not found at %s'% maven_file_path)
            return None

    def last_modified(self, artifact):
        maven_file_path = self.get_artifact_uri(artifact, 'pom')
        if os.path.exists(maven_file_path):
            last_modify = os.stat(maven_file_path)[stat.ST_MTIME]
            return last_modify
        else:
            return None

class MavenHttpRemoteRepos(MavenRepos):
    def __init__(self, name, uri):
        MavenRepos.__init__(self, name, uri)
        self.pom_cache = {}

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
        if artifact in self.pom_cache:
            return self.pom_cache[artifact]

        if artifact.is_snapshot():
            snapshot_info = self.get_snapshot_info(artifact)
            if snapshot_info is not None:
                ts, bn = snapshot_info
                artifact.timestamp = ts
                artifact.build_number = bn

        maven_path = self.get_artifact_uri(artifact, 'pom')
        try:
            logger.info('Opening pom file %s'% maven_path)
            f = urllib2.urlopen(maven_path)
            data =  f.read()
            f.close()
            
            ## cache
            self.pom_cache[artifact] = data

            return data
        except urllib2.HTTPError:
            logger.info('Pom file not found at %s'% maven_path)
            return None

    def get_artifact_uri(self, artifact, ext):
        if not artifact.is_snapshot():
            maven_name = artifact.to_maven_name(ext)
        else:
            maven_name = artifact.to_maven_snapshot_name(ext)
        maven_path = self.uri + maven_name
        return maven_path

    def get_snapshot_info(self, artifact):
        metadata_path = self.get_metadata_path(artifact) 

        try:
            f = urllib2.urlopen(metadata_path)
            data = f.read()
            f.close()

            eletree = ElementTree.fromstring(data)
            timestamp = eletree.findtext('versioning/snapshot/timestamp')
            build_number = eletree.findtext('versioning/snapshot/buildNumber')
            
            return (timestamp, build_number)
        except urllib2.HTTPError:
            return None

    def get_metadata_path(self, artifact):
        group = artifact.group.replace('.', '/')
        metadata_path = "%s/%s/%s/%s/maven-metadata.xml" % (self.uri, group, 
                artifact.artifact, artifact.version)
        return metadata_path

    def last_modified(self, artifact):
        metadata_path = self.get_metadata_path(artifact) 
        try:
            fd = urllib2.urlopen(metadata_path)
            if 'last-modified' in fd.headers:
                ts = fd.headers['last-modified']
                fd.close()
                locale.setlocale(locale.LC_TIME, 'en_US')
                last_modified = time.strptime(ts, '%a, %d %b %Y %H:%M:%S %Z')
                return time.mktime(last_modified)
            else:
                fd.close()
                return 0
        except urllib2.HTTPError:
            return None

    def download_check_sum(self, checksum_type, origin_file_name):
        """ return pre calculated checksum value, only avaiable for remote repos """
        checksum_url = origin_file_name + "." + checksum_type
        try:
            f = urllib2.urlopen(checksum_url)
            data = f.read()
            f.close()
            return data
        except urllib2.HTTPError:
            return None

    def checksum(self, filepath, checksum_type):
        if checksum_type == 'md5':
            hasher = hashlib.md5()
        elif checksum_type == 'sha1':
            hasher = hashlib.sha1()

        buf_size = 1024*8
        file_to_check = file(filepath, 'r')
        buf = file_to_check.read(buf_size)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file_to_check.read(buf_size)

        file_to_check.close()
        return hasher.hexdigest()

def _create_repos(name, uri, repos_type):
    if repos_type == 'local':
        return MavenFileSystemRepos(name, uri)
    if repos_type == 'remote':
        return MavenHttpRemoteRepos(name, uri)

def _load_config():
    default_config = os.path.expanduser('~/.jip')
    if os.path.exists(default_config):
        config = ConfigParser()
        config.read(default_config)

        repos = []
        ## only loop section starts with "repos:"
        repos_sections = filter(lambda x:x.startswith("repos:"), config.sections())
        for section in repos_sections:
            name = section.split(':')[1]
            uri = config.get(section, "uri")
            rtype = config.get(section, "type")
            repos.append((name, uri, rtype))
        return repos
    else:
        return None

## allow custom repository configuration from a config file
MAVEN_REPOS = map(lambda x: _create_repos(*x), 
        _load_config() or [MAVEN_LOCAL_REPOS, MAVEN_PUBLIC_REPOS])

class Pom(object):
    def __init__(self, pom_string):
        self.pom_string = pom_string
        self.eletree = None
        self.properties = None
        self.dep_mgmt = None
        self.parent = None

    def get_element_tree(self):
        if self.eletree is None:
            ## we use this dirty method to remove namesapce attribute so that elementtree will use default empty namespace
            pom_string = re.sub(r"<project(.|\s)*?>", '<project>', self.pom_string, 1)
            self.eletree = ElementTree.fromstring(pom_string)
        return self.eletree

    def get_parent_pom(self):
        if self.parent is not None:
            return self.parent

        eletree = self.get_element_tree()
        parent = eletree.find("parent")
        if parent is not None:
            parent_group_id = parent.findtext("groupId")
            parent_artifact_id = parent.findtext("artifactId")
            parent_version_id = parent.findtext("version")

            artifact = Artifact(parent_group_id, parent_artifact_id, parent_version_id)
            global MAVEN_REPOS
            for repos in MAVEN_REPOS:
                parent_pom = repos.download_pom(artifact)
                if parent_pom is not None:
                    break

            if parent_pom is not None:
                self.parent = Pom(parent_pom)
                return self.parent
            else:
                logger.error("cannot find parent pom %s" % parent_pom)
                sys.exit(1)
        else:
            return None

    def get_dependency_management(self):
        if self.dep_mgmt is not None:
            return self.dep_mgmt

        dependency_management_version_dict = {}

        parent = self.get_parent_pom()
        if parent is not None:
            dependency_management_version_dict.update(parent.get_dependency_management())

        properties = self.get_properties()
        eletree = self.get_element_tree()
        dependency_management_dependencies = eletree.findall("dependencyManagement/dependencies/dependency")
        for dependency in dependency_management_dependencies:
            group_id = self.__resolve_placeholder(dependency.findtext("groupId"), properties)
            artifact_id = self.__resolve_placeholder(dependency.findtext("artifactId"), properties)
            version = self.__resolve_placeholder(dependency.findtext("version"), properties)

            scope = dependency.findtext("scope")
            if scope is not None and scope == 'import':
                artifact = Artifact(group_id, artifact_id, version)
                global MAVEN_REPOS
                for repos in MAVEN_REPOS:
                    import_pom = repos.download_pom(artifact)
                    if import_pom is not None:
                        break
                if import_pom is not None:
                    import_pom = Pom(import_pom)
                    dependency_management_version_dict.update(import_pom.get_dependency_management())
                else:
                    logger.error("can not find dependency management import: %s" % artifact)
                    sys.exit(1)
            else:
                dependency_management_version_dict[(group_id, artifact_id)] = version

        self.dep_mgmt = dependency_management_version_dict
        return dependency_management_version_dict

    def get_dependencies(self):
        dep_mgmt = self.get_dependency_management()
        props = self.get_properties()
        eletree = self.get_element_tree()

        runtime_dependencies = []

        dependencies = eletree.findall("dependencies/dependency")
        for dependency in dependencies:
            # resolve placeholders in pom (properties and pom references)
            group_id = self.__resolve_placeholder(dependency.findtext("groupId"), props)
            artifact_id = self.__resolve_placeholder(dependency.findtext("artifactId"), props)
            version = dependency.findtext("version")
            if version is not None:
                version = self.__resolve_placeholder(version, props)

            scope = dependency.findtext("scope") or ''
            optional = dependency.findtext("optional") or ''

            # runtime dependency
            if (scope == '' or scope == 'compile' or scope == 'runtime') and (optional == '' or optional == 'false'):
                if version is None:
                    version = dep_mgmt[(group_id, artifact_id)]
                artifact = Artifact(group_id, artifact_id, version)
                runtime_dependencies.append(artifact)

        logger.debug('Find dependencies: %s'% runtime_dependencies)
        return runtime_dependencies

    def get_properties(self):
        if self.properties is not None:
            return self.properties

        eletree = self.get_element_tree()
        # parsing in-pom properties
        properties = {}
        properties_ele = eletree.find("properties")
        if properties_ele is not None:
            prop_eles = properties_ele.getchildren()
            for prop_ele in prop_eles:
                if prop_ele.tag == 'property':
                    name = prop_ele.get("name")
                    value = prop_ele.get("value")
                else:
                    name = prop_ele.tag
                    value = prop_ele.text
                properties[name] = value

        parent = self.get_parent_pom()
        if parent is not None:
            properties.update(parent.get_properties())

        ## pom specific elements
        groupId = eletree.findtext('groupId')
        artifactId = eletree.findtext('artifactId')
        version = eletree.findtext('version')
        if version is None:
            version = eletree.findtext('parent/version')

        properties["project.groupId"] = groupId
        properties["project.artifactId"] = artifactId
        properties["project.version"] = version

        properties["pom.groupId"] = groupId
        properties["pom.artifactId"] = artifactId
        properties["pom.version"] = version
        self.properties = properties
        return properties

    def __resolve_placeholder(self, text, properties):
       def subfunc(matchobj):
            key = matchobj.group(1)
            if key in properties:
                return properties[key]
            else:
                return matchobj.group(0)
       return re.sub(r'\$\{(.*?)\}', subfunc, text)

def _install(*artifacts):
    global MAVEN_REPOS    
    ## ready set contains artifact jip file names
    ready_set = os.listdir(DEFAULT_JAVA_LIB_PATH)
    
    ## dependency_set and installed_set contain artifact objects
    dependency_set = set()
    installed_set = set()

    for a in artifacts:
        dependency_set.add(a)

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
                    ready_set.append(artifact.to_jip_name())
                found = True

                pom_obj = Pom(pom)
                more_dependencies = pom_obj.get_dependencies()
                for d in more_dependencies: dependency_set.add(d)
                break
        
        if not found:
            logger.error("Artifact not found in repositories: %s", artifact)
            sys.exit(1)

def install(artifact_identifier):
    """Install a package with maven coordinate "groupId:artifactId:version" """
    group, artifact, version = artifact_identifier.split(":")
    artifact_to_install = Artifact(group, artifact, version)

    _install(artifact_to_install)

def clean():
    """ Remove all downloaded packages """
    logger.info("remove java libs in %s" % DEFAULT_JAVA_LIB_PATH)
    shutil.rmtree(DEFAULT_JAVA_LIB_PATH)

## another resolve task, allow jip to resovle dependencies from a pom file.
def resolve(pomfile):
    """ Resolve and download dependencies in pom file """
    pomfile = open(pomfile, 'r')
    pomstring = pomfile.read()
    pom = Pom(pomstring)

    dependencies = pom.get_dependencies()
    _install(*dependencies)

def update(artifact_id):
    """ update a snapshot artifact, check for new version """
    group, artifact, version = artifact_id.split(":")
    artifact = Artifact(group, artifact, version)

    global MAVEN_REPOS    
    if artifact.is_snapshot():
        installed_file = os.path.join(DEFAULT_JAVA_LIB_PATH, artifact.to_jip_name())
        if os.path.exists(installed_file):
            lm = os.stat(installed_file)[stat.ST_MTIME]

            ## find the repository contains the new release
            selected_repos = None
            for repos in MAVEN_REPOS:
                ts = repos.last_modified(artifact)
                if ts is not None and ts > lm :
                    lm = ts
                    selected_repos = repos
            
            if selected_repos is not None:
                ## download new jar
                selected_repos.download_jar(artifact)

                ## try to update dependencies
                pomstring = selected_repos.download_pom(artifact)
                pom = Pom(pomstring)
                dependencies = pom.get_dependencies()
                _install(*dependencies)

        else:
            logger.error('Artifact not installed: %s' % artifact)
    else:
        logger.error('Can not update non-snapshot artifact')
        return


commands = {
        "install": install,
        "clean": clean,
        "resolve": resolve,
        "update": update,
        }

def parse_cmd(argus):
    if len(argus) > 0:
        cmd = argus[0]
        values = argus[1:]
        return (cmd, values)
    else:
        return (None, None)

def print_help():
    print "Available commands:"
    for name, func in commands.items():
        print "\t%s\t\t%s" % (name, func.__doc__)

def main():
    logger.debug("sys args %s" % sys.argv)
    args = sys.argv[1:] 
    cmd, values = parse_cmd(args)
    if cmd in commands:
        commands[cmd](*values)
    else:
        print_help()
        
if __name__ == "__main__":
    main()
