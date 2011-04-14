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
import shutil
import urllib2
import re
import locale
import stat
import time
import hashlib
from xml.etree import ElementTree
from string import Template
from ConfigParser import ConfigParser

from . import logger, get_virtual_home

class RepositoryManager(object):
    MAVEN_LOCAL_REPOS = ('local', os.path.expanduser('~/.m2/repository'), 'local')
    MAVEN_PUBLIC_REPOS = ('public', "http://repo1.maven.org/maven2/", 'remote')
    def __init__(self):
        self.repos = []

    def add_repos(self, name, uri, repos_type, order=-1):
        if repos_type == 'local':
            repo = MavenFileSystemRepos(name, uri)
        elif repos_type == 'remote':
            repo = MavenHttpRemoteRepos(name, uri)
        else:
            logger.warn('[Error] Unknown repository type.')
            sys.exit(1)

        if repo not in self.repos:
            self.repos.insert(order, repo)

    def _load_config(self):
        config_file_path = os.path.join(get_virtual_home(), '.jip')
        if not os.path.exists(config_file_path):
            config_file_path = os.path.expanduser('~/.jip')
        if os.path.exists(config_file_path):
            config = ConfigParser()
            config.read(config_file_path)

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

    def init_repos(self):
        for repo in (self._load_config() or [self.MAVEN_LOCAL_REPOS, self.MAVEN_PUBLIC_REPOS]):
            ## create repos in order
            name, uri, rtype = repo
            self.add_repos(name, uri, rtype, order=len(self.repos))

## globals
repos_manager = RepositoryManager()
    

class Artifact(object):
    def __init__(self, group, artifact, version):
        self.group = group
        self.artifact = artifact
        self.version = version
        self.timestamp = None
        self.build_number = None
        self.exclusions = []
        self.repos = None

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

#    def __hash__(self):
#        return self.group.__hash__()*13+self.artifact.__hash__()*7+self.version.__hash__()

    def is_snapshot(self):
        return self.version.find('SNAPSHOT') > 0

    def is_same_artifact(self, other):
        if isinstance(other, Artifact):
            ## need to support wildcard
            group_match = True if self.group == '*' or other.group == '*' else self.group == other.group
            artif_match = True if self.artifact == '*' or other.artifact == '*' else self.artifact == other.artifact
            return group_match and artif_match
        else:
            return False

    @classmethod
    def from_id(cls, artifact_id):
        group, artifact, version = artifact_id.split(":")
        artifact = Artifact(group, artifact, version)
        return artifact

class MavenRepos(object):
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri

    def __eq__(self, other):
        if isinstance(other, MavenRepos):
            return self.uri == other.uri
        else:
            return False

    def get_artifact_uri(self, artifact, ext):
        pass

    def download_jar(self, artifact, local_path=None):
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

    def download_jar(self, artifact, local_path=None):
        maven_file_path = self.get_artifact_uri(artifact, 'jar')
        logger.info("[Checking] jar package from %s" % self.name)
        if os.path.exists(maven_file_path):
            local_jip_path = local_path+"/"+artifact.to_jip_name()
            logger.info("[Downloading] %s" % maven_file_path)
            shutil.copy(maven_file_path, local_jip_path)
            logger.info("[Finished] %s completed" % local_jip_path)
        else:
            logger.error("[Error] File not found %s" % maven_file_path)
            raise IOError('File not found:' + maven_file_path)

    def download_pom(self, artifact):
        maven_file_path = self.get_artifact_uri(artifact, 'pom')
        logger.info('[Checking] pom file %s'% maven_file_path)
        if os.path.exists(maven_file_path):
            pom_file = open(maven_file_path, 'r')
            data =  pom_file.read()
            pom_file.close()
            return data
        else:
            logger.info('[Skipped] pom file not found at %s' % maven_file_path)
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

    def download_jar(self, artifact, local_path=None):
        maven_path = self.get_artifact_uri(artifact, 'jar')
        logger.info('[Downloading] jar from %s' % maven_path)
        f = urllib2.urlopen(maven_path)
        data =  f.read()
        f.close()

        local_jip_path = local_path+"/"+artifact.to_jip_name()
        local_f = open(local_jip_path, 'w')
        local_f.write(data)
        local_f.close()
        logger.info('[Finished] %s downloaded ' % maven_path)

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
            logger.info('[Checking] pom file %s'% maven_path)
            f = urllib2.urlopen(maven_path)
            data =  f.read()
            f.close()
            
            ## cache
            self.pom_cache[artifact] = data

            return data
        except urllib2.HTTPError:
            logger.info('[Skipped] Pom file not found at %s'% maven_path)
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
            global repos_manager
            for repos in repos_manager.repos:
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
                global repos_manager
                for repos in repos_manager.repos:
                    import_pom = repos.download_pom(artifact)
                    if import_pom is not None:
                        break
                if import_pom is not None:
                    import_pom = Pom(import_pom)
                    dependency_management_version_dict.update(import_pom.get_dependency_management())
                else:
                    logger.error("[Error] can not find dependency management import: %s" % artifact)
                    sys.exit(1)
            else:
                ## will also remember scope for scope inheritance
                dependency_management_version_dict[(group_id, artifact_id)] = (version, scope)

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
            
            scope = dependency.findtext("scope")
            optional = dependency.findtext("optional")

            ### dependency exclusion           
            ### there is no `version` in a exclusion definition
            exclusions = []
            for exclusion in dependency.findall("exclusions/exclusion"):
                groupId = exclusion.findtext("groupId")
                artifactId = exclusion.findtext("artifactId")
                excluded_artifact = Artifact(groupId, artifactId, None)
                exclusions.append(excluded_artifact)

            # runtime dependency
            if optional is None or optional == 'false':
                if version is None:
                    version = dep_mgmt[(group_id, artifact_id)][0]
                if scope is None:
                    ## bug fix, scope is an optional attribute
                    if (group_id, artifact_id) in dep_mgmt:
                        scope = dep_mgmt[(group_id, artifact_id)][1]
                if scope in (None, 'runtime', 'compile'):
                    artifact = Artifact(group_id, artifact_id, version)
                    artifact.exclusions = exclusions
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

    def get_repositories(self):
        eletree = self.get_element_tree()

        repositories = eletree.findall("repositories/repository")
        repos = []
        for repository in repositories:
            name = repository.findtext("id")
            uri = repository.findtext("url")
            repos.append((name, uri, "remote"))
        return repos
