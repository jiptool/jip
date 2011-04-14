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
import stat

from . import logger, JIP_VERSION, get_lib_path, get_virtual_home
from jip.maven import repos_manager, Pom, Artifact
from jip.search import searcher
from jip.index import index_manager

## command dictionary {name: function}
commands = {}
def command(register=True):
    def _command(func):
        ## init default repos before running command
        def wrapper(*args, **kwargs):
            repos_manager.init_repos()
            index_manager.initialize()
            func(*args, **kwargs)
            index_manager.finalize()
        ## register in command dictionary        
        if register:
            commands[func.__name__.replace('_','-')] = wrapper
            wrapper.__doc__ = func.__doc__
        return wrapper
    return _command

def _install(*artifacts):
    
    ## dependency_set and installed_set contain artifact objects
    dependency_set = set()

    for a in artifacts:
        dependency_set.add(a)

    while len(dependency_set) > 0:
        artifact = dependency_set.pop()

        ## to prevent multiple version installed
        ## TODO we need a better strategy to resolve this
        if index_manager.is_same_installed(artifact):
            continue

        found = False
        for repos in repos_manager.repos:

            pom = repos.download_pom(artifact)

            ## find the artifact
            if pom is not None:
                if not index_manager.is_installed(artifact):
                    repos.download_jar(artifact, get_lib_path())
                    artifact.repos = repos
                    index_manager.add_artifact(artifact)
                found = True

                pom_obj = Pom(pom)
                more_dependencies = pom_obj.get_dependencies()
                for d in more_dependencies:
                    d.exclusions.extend(artifact.exclusions)
                    if not index_manager.is_same_installed(d):
                        dependency_set.add(d)
                break
        
        if not found:
            logger.error("[Error] Artifact not found: %s", artifact)
            sys.exit(1)


@command()
def install(artifact_id):
    """ Install a package identified by "groupId:artifactId:version" """
    artifact = Artifact.from_id(artifact_id)

    _install(artifact)
    logger.info("[Finished] %s successfully installed" % artifact_id)

@command()
def clean():
    """ Remove all downloaded packages """
    logger.info("[Deleting] remove java libs in %s" % get_lib_path())
    shutil.rmtree(get_lib_path())
    index_manager.remove_all()
    logger.info("[Finished] all downloaded files erased")

## another resolve task, allow jip to resovle dependencies from a pom file.
@command()
def resolve(pomfile):
    """ Resolve and download dependencies in pom file """
    pomfile = open(pomfile, 'r')
    pomstring = pomfile.read()
    pom = Pom(pomstring)
    ## custom defined repositories
    repositories = pom.get_repositories()
    for repos in repositories:
        repos_manager.add_repos(*repos)

    dependencies = pom.get_dependencies()
    _install(*dependencies)
    logger.info("[Finished] all dependencies resolved")

@command()
def update(artifact_id):
    """ Update a snapshot artifact, check for new version """
    artifact = Artifact.from_id(artifact_id)
    artifact = index_manager.get_artifact(artifact)
    if artifact is None:
        logger.error('[Error] Can not update %s, please install it first' % artifact)
        sys.exit(1)

    if artifact.is_snapshot():
        selected_repos = artifact.repos
        installed_file = os.path.join(get_lib_path(), artifact.to_jip_name())
        if os.path.exists(installed_file):
            lm = os.stat(installed_file)[stat.ST_MTIME]

            ## find the repository contains the new release
            ts = selected_repos.last_modified(artifact)
            if ts is not None and ts > lm :
                ## download new jar
                selected_repos.download_jar(artifact, get_lib_path())

                ## try to update dependencies
                pomstring = selected_repos.download_pom(artifact)
                pom = Pom(pomstring)
                dependencies = pom.get_dependencies()
                _install(*dependencies)
            logger.info('[Finished] Artifact snapshot %s updated' % artifact_id)
        else:
            logger.error('[Error] Artifact not installed: %s' % artifact)
            sys.exit(1)
    else:
        logger.error('[Error] Can not update non-snapshot artifact')
        return

@command()
def version():
    """ Display jip version """
    logger.info('[Version] jip %s, jython %s' % (JIP_VERSION, sys.version))

@command()
def deps(artifact_id):
    """ Install dependencies for a given artifact coordinator """
    artifact = Artifact.from_id(artifact_id)

    found = False
    for repos in repos_manager.repos:
        pom_raw = repos.download_pom(artifact)
        ## find the artifact
        if pom_raw is not None:
            pom = Pom(pom_raw)
            found = True
            _install(*pom.get_dependencies())
            break

    if not found:
        logger.error('[Error] artifact %s not found in any repository' % artifact_id)
        sys.exit(1)
    else:
        logger.info('[Finished] finished resolve dependencies for %s ' % artifact_id)

@command()
def search(query):
    """ Search maven central repository with keywords"""
    logger.info('[Searching] "%s" in Maven central repository...' % query)
    results = searcher.search(query)
    if len(results) > 0:
        for item in results:
            g,a,v,p = item
            print "%s-%s (%s)\n\t%s:%s:%s" % (a,v,p,g,a,v)
    else:
        logger.info('[Finished] nothing returned by criteria "%s"' % query)

@command()
def list():
    """ List current installed artifacts """
    index_manager.keep_consistent()
    for a in index_manager.installed:
        print "%s" % a

@command()
def remove(artifact_id):
    """ Remove an artifact from library path """
    logger.info('[Checking] %s in library index' % artifact_id)
    artifact = Artifact.from_id(artifact_id)
    artifact_path = os.path.join(get_lib_path(), artifact.to_jip_name())

    if index_manager.is_installed(artifact) and os.path.exists(artifact_path):
        os.remove(artifact_path)
        index_manager.remove_artifact(artifact)
        logger.info('[Finished] %s removed from library path' % artifact_id)
    else:
        logger.error('[Error] %s not installed' % artifact_id)
        sys.exit(1)


