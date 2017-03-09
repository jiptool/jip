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

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
from string import Template
import os
import locale
import shutil
import stat
import time
import hashlib
try:
    import urllib.error as urlerror
    import urllib.request as urlrequest
except ImportError:
    import urllib2 as urlerror
    import urllib2 as urlrequest
from xml.etree import ElementTree

from jip import logger
from jip.util import DownloadException, download, download_string, get_virtual_home

class RepositoryManager(object):
    MAVEN_LOCAL_REPOS = ('local', os.path.expanduser(os.path.join('~', '.m2', 'repository')), 'local')
    MAVEN_PUBLIC_REPOS = ('public', "http://repo1.maven.org/maven2/", 'remote')
    def __init__(self):
        self.repos = []

    def add_repos(self, name, uri, repos_type, order=None):
        if repos_type == 'local':
            repo = MavenFileSystemRepos(name, uri)
        elif repos_type == 'remote':
            repo = MavenHttpRemoteRepos(name, uri)
        else:
            logger.warn('[Error] Unknown repository type.')
            sys.exit(1)

        if repo not in self.repos:
            if order is not None:
                self.repos.insert(order, repo)
            else:
                self.repos.append(repo)
            logger.debug('[Repository] Added: %s' % repo.name)

    def _load_config(self):
        config_file_path = os.path.join(get_virtual_home(), '.jip_config')
        if not os.path.exists(config_file_path):
            config_file_path = os.path.expanduser(os.path.join('~', '.jip_config'))
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
        for repo in (self._load_config() or [self.MAVEN_PUBLIC_REPOS]):
            ## create repos in order
            name, uri, rtype = repo
            self.add_repos(name, uri, rtype, order=len(self.repos))

    def to_pom(self):
        pom_template = Template("""
        <repository>
            <id>$repoId</id>
            <name>$repoId</name>
            <url>$url</url>
        </repository>""")
        reps = []
        for repo in self.repos:
            ### remote only
            if isinstance(repo, MavenHttpRemoteRepos):
                ### remote repository other than default
                if repo.uri != self.MAVEN_PUBLIC_REPOS[1]:
                    content = pom_template.substitute({'repoId':repo.name,
                        'url': repo.uri})
                    reps.append(content)
        return ''.join(reps)


## globals
repos_manager = RepositoryManager()

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

    def download_jar(self, artifact, local_path):
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
        MavenRepos.__init__(self, name, os.path.expanduser(uri))

    def get_artifact_uri(self, artifact, ext):
        maven_name = artifact.to_maven_name(ext)
        maven_file_path = os.path.join(self.uri,maven_name)
        return maven_file_path

    def download_jar(self, artifact, local_path):
        maven_file_path = self.get_artifact_uri(artifact, 'jar')
        logger.info("[Checking] jar package from %s" % self.name)
        if os.path.exists(maven_file_path):
            local_jip_path = os.path.join(local_path, artifact.to_jip_name())
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
        self.pom_not_found_cache = []

    def download_jar(self, artifact, local_path):
        maven_path = self.get_artifact_uri(artifact, 'jar')
        logger.info('[Downloading] jar from %s' % maven_path)
        local_jip_path = os.path.join(local_path, artifact.to_jip_name())
        local_f = open(local_jip_path, 'wb')
        ## download jar asyncly
        download(maven_path, local_f, True)
        ##logger.info('[Finished] %s downloaded ' % maven_path)

    def download_pom(self, artifact):
        if artifact in self.pom_not_found_cache:
            return None

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
            data = download_string(maven_path)
            ## cache
            self.pom_cache[artifact] = data

            return data
        except DownloadException:
            self.pom_not_found_cache.append(artifact)
            logger.info('[Skipped] Pom file not found at %s'% maven_path)
            return None

    def get_artifact_uri(self, artifact, ext):
        if not artifact.is_snapshot():
            maven_name = artifact.to_maven_name(ext)
        else:
            maven_name = artifact.to_maven_snapshot_name(ext)
        if self.uri.endswith('/'):
            maven_path = self.uri + maven_name
        else:
            maven_path = self.uri + '/' + maven_name
        return maven_path

    def get_snapshot_info(self, artifact):
        metadata_path = self.get_metadata_path(artifact)

        try:
            data = download_string(metadata_path)

            eletree = ElementTree.fromstring(data)
            timestamp = eletree.findtext('versioning/snapshot/timestamp')
            build_number = eletree.findtext('versioning/snapshot/buildNumber')

            return (timestamp, build_number)
        except DownloadException:
            return None

    def get_metadata_path(self, artifact):
        group = artifact.group.replace('.', '/')
        metadata_path = "%s/%s/%s/%s/maven-metadata.xml" % (self.uri, group,
                artifact.artifact, artifact.version)
        return metadata_path

    def last_modified(self, artifact):
        metadata_path = self.get_metadata_path(artifact)
        try:
            fd = urlrequest.urlopen(metadata_path)
            if 'last-modified' in fd.headers:
                ts = fd.headers['last-modified']
                fd.close()
                locale.setlocale(locale.LC_TIME, 'en_US')
                last_modified = time.strptime(ts, '%a, %d %b %Y %H:%M:%S %Z')
                return time.mktime(last_modified)
            else:
                fd.close()
                return 0
        except urlerror.HTTPError:
            return None

    def download_check_sum(self, checksum_type, origin_file_name):
        """ return pre calculated checksum value, only avaiable for remote repos """
        checksum_url = origin_file_name + "." + checksum_type
        try:
            return download_string(checksum_url)
        except DownloadException:
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
