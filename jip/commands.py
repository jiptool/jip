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
import inspect
from string import Template

from jip import repos_manager, index_manager, logger,\
        JIP_VERSION, __path__, pool, cache_manager
from jip.maven import Pom, Artifact
from jip.util import get_lib_path, get_virtual_home

## command dictionary {name: function}
commands = {}

## options [(name, nargs, description, option_type), ...]
def command(register=True, options=[]):
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
            wrapper.__doc__ = inspect.getdoc(func)
            wrapper.__raw__ = func

            ### inspect arguments
            args = inspect.getargspec(func)
            defaults = list(args[3]) if args[3] else []
            wrapper.args = []

            for argidx in range(len(args[0])-1, -1, -1):
                if args[0][argidx] != 'options':
                    default_value = defaults.pop() if defaults else None
                    wrapper.args.append((args[0][argidx], default_value))
                    wrapper.args.reverse()
                else:
                    ## options should have default value {}
                    ## so remove this one for counter
                    defaults.pop()

            ### addtional options
            wrapper.options = options

        return wrapper
    return _command

def _find_pom(artifact):
    """ find pom and repos contains pom """
    ## lookup cache first
    if cache_manager.is_artifact_in_cache(artifact):
        pom = cache_manager.get_artifact_pom(artifact)       
        return (pom, cache_manager.as_repos())
    else:
        for repos in repos_manager.repos:
            pom = repos.download_pom(artifact)
            ## find the artifact
            if pom is not None:
                cache_manager.put_artifact_pom(artifact, pom)
                return (pom, repos)
        return None            

def _resolve_artifacts(artifacts, exclusions=[]):
    ## download queue
    download_list = []

    ## dependency_set contains artifact objects to resolve
    dependency_set = set()

    for a in artifacts:
        dependency_set.add(a)

    while len(dependency_set) > 0:
        artifact = dependency_set.pop()

        ## to prevent multiple version installed
        ## TODO we need a better strategy to resolve this
        if index_manager.is_same_installed(artifact)\
                and artifact not in download_list:
            continue

        pominfo = _find_pom(artifact)
        if pominfo is None:
            logger.error("[Error] Artifact not found: %s", artifact)
            sys.exit(1)

        if not index_manager.is_installed(artifact):
            pom, repos = pominfo

            # repos.download_jar(artifact, get_lib_path())
            artifact.repos = repos

            # skip excluded artifact
            if not any(map(artifact.is_same_artifact, exclusions)):
                download_list.append(artifact)
                index_manager.add_artifact(artifact)

            pom_obj = Pom(pom)
            for r in pom_obj.get_repositories():
                repos_manager.add_repos(*r)

            more_dependencies = pom_obj.get_dependencies()
            for d in more_dependencies:
                d.exclusions.extend(artifact.exclusions)
                if not index_manager.is_same_installed(d):
                    dependency_set.add(d)
        
    return download_list

def _install(artifacts, exclusions=[], options={}):
    dryrun = options.get("dry-run", False)
    _exclusions = options.get('exclude', [])
    if _exclusions:
        _exclusions = map(lambda x: Artifact(*(x.split(":"))), _exclusions)
        exclusions.extend(_exclusions)

    download_list = _resolve_artifacts(artifacts, exclusions)
    
    if not dryrun:
        ## download to cache first
        for artifact in download_list:
            if artifact.repos != cache_manager.as_repos():
                artifact.repos.download_jar(artifact, 
                        cache_manager.get_jar_path(artifact))
        pool.join()
        for artifact in download_list:
            cache_manager.get_artifact_jar(artifact, get_lib_path())

        index_manager.commit()
        logger.info("[Finished] dependencies resolved")
    else:
        logger.info("[Install] Artifacts to install:")
        for artifact in download_list:
            logger.info(artifact)

@command(options=[
    ("dry-run", 0, "perform a command without actual download", bool),
    ("exclude", "+", "exclude artifacts in install, for instance, 'junit:junit'", str)
])
def install(artifact_id, options={}):
    """ Install a package identified by "groupId:artifactId:version" """
    artifact = Artifact.from_id(artifact_id)

    _install([artifact], options=options)

@command()
def clean():
    """ Remove all downloaded packages """
    logger.info("[Deleting] remove java libs in %s" % get_lib_path())
    shutil.rmtree(get_lib_path())
    index_manager.remove_all()
    index_manager.commit()
    logger.info("[Finished] all downloaded files erased")

## another resolve task, allow jip to resovle dependencies from a pom file.
@command(options=[
    ("dry-run", 0, "perform a command without actual download", bool)
])
def resolve(pomfile, options={}):
    """ Resolve and download dependencies in pom file """
    pomfile = open(pomfile, 'r')
    pomstring = pomfile.read()
    pom = Pom(pomstring)
    ## custom defined repositories
    repositories = pom.get_repositories()
    for repos in repositories:
        repos_manager.add_repos(*repos)

    dependencies = pom.get_dependencies()
    _install(dependencies, options=options)

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
                _install(dependencies)
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

@command(options=[
    ("dry-run", 0, "perform a command without actual download", bool)
])
def deps(artifact_id, options={}):
    """ Install dependencies for a given artifact coordinator """
    artifact = Artifact.from_id(artifact_id)
    pominfo = _find_pom(artifact)
    if pominfo is not None:
        pom = Pom(pominfo[0])
        _install(pom.get_dependencies(), options=options)
    else:
        logger.error('[Error] artifact %s not found in any repository' % artifact_id)
        sys.exit(1)

@command(options=[
    ('group', '?', "group name", str),
    ('artifact', '?', "artifact name", str)
])
def search(query="", options={}):
    """ Search maven central repository with keywords"""
    from .search import searcher
    if query is not None and len(query) > 0:
        logger.info('[Searching] "%s" in Maven central repository...' % query)
        results = searcher.search(query)
    else:
        g = options.get('group', '')
        a = options.get('artifact', '')
        logger.info('[Searching] "%s:%s" in Maven central repository...' % (g,a))
        results = searcher.search_group_artifact(g, a)
    if len(results) > 0:
        for item in results:
            g,a,v,p = item
            logger.info("%s-%s (%s)\n\t%s:%s:%s" % (a,v,p,g,a,v))
    else:
        logger.info('[Finished] nothing returned by criteria "%s"' % query)

@command()
def list():
    """ List current installed artifacts """
    index_manager.keep_consistent()
    for a in index_manager.installed:
        logger.info("%s" % a)

@command()
def remove(artifact_id):
    """ Remove an artifact from library path """
    logger.info('[Checking] %s in library index' % artifact_id)
    artifact = Artifact.from_id(artifact_id)
    artifact_path = os.path.join(get_lib_path(), artifact.to_jip_name())

    if index_manager.is_installed(artifact) and os.path.exists(artifact_path):
        os.remove(artifact_path)
        index_manager.remove_artifact(artifact)
        index_manager.commit()
        logger.info('[Finished] %s removed from library path' % artifact_id)
    else:
        logger.error('[Error] %s not installed' % artifact_id)
        sys.exit(1)

@command()
def freeze():
    """ Dump current configuration to a pom file """
    dependencies = index_manager.to_pom()
    repositories = repos_manager.to_pom()
    template = Template(open(os.path.join(__path__[0], '../data/pom.tpl'), 'r').read())
    logger.info( template.substitute({'dependencies': dependencies,
        'repositories': repositories}))
