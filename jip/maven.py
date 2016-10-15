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
import re
from xml.etree import ElementTree
from string import Template, whitespace

from . import logger, repos_manager, cache_manager

class Artifact(object):
    def __init__(self, group, artifact, version=None):
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

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        ## python3 set requires a custom hash function to ensure item hash unchanged
        ## however, python2 pickle module might call this function before internal
        ## propertoes loaded. So here we return 0 if no key property loaded as a workaround
        if hasattr(self, 'group') and hasattr(self, 'artifact') and hasattr(self, 'version'):
            return self.group.__hash__()*13+self.artifact.__hash__()*7+self.version.__hash__()
        else:
            return 0

    def is_snapshot(self):
        return self.version.find('SNAPSHOT') > 0

    def is_same_artifact(self, other):
       ## need to support wildcard
       group_match = True if self.group == '*' or other.group == '*' else self.group == other.group
       artif_match = True if self.artifact == '*' or other.artifact == '*' else self.artifact == other.artifact
       return group_match and artif_match

    @classmethod
    def from_id(cls, artifact_id):
        group, artifact, version = artifact_id.split(":")
        artifact = Artifact(group, artifact, version)
        return artifact


class WhitespaceNormalizer(ElementTree.TreeBuilder, object):   # The target object of the parser
     def data(self, data):
         data=data.strip(whitespace)         #strip whitespace at start and end of string
         return super(WhitespaceNormalizer,self).data(data)

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
            parser = ElementTree.XMLParser(target=WhitespaceNormalizer())
            parser.feed(pom_string)
            self.eletree = parser.close()
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
            if cache_manager.is_artifact_in_cache(artifact, jar=False):
                parent_pom = cache_manager.get_artifact_pom(artifact)
            else:
                for repos in repos_manager.repos:
                    parent_pom = repos.download_pom(artifact)
                    if parent_pom is not None:
                        cache_manager.put_artifact_pom(artifact, parent_pom)
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

            version_val = version
            while True:
                try:
                    version = version_val if version_val != None else version
                    version_val = properties.get(version_val[2:-1])
                except TypeError:
                    break


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
        if groupId is None:
            groupId = eletree.findtext('parent/groupId')

        properties["project.parent.version"] = eletree.findtext('parent/version')
        properties["project.parent.groupId"] = eletree.findtext('parent/groupId')
        properties["project.groupId"] = self.__resolve_placeholder(groupId, properties)
        properties["project.artifactId"] = artifactId
        properties["project.version"] = self.__resolve_placeholder(version, properties)

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
