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

import sys

from jip import cache_manager, repos_manager, pool
from jip.commands import _resolve_artifacts
from jip.maven import Artifact

__all__ = ['require']

def _prepare():
    repos_manager.init_repos()

def require(artifact_id):
    _prepare()

    artifact = Artifact.from_id(artifact_id)
    artifact_set = _resolve_artifacts([artifact])

    ## download to cache first
    for artifact in artifact_set:
        if artifact.repos != cache_manager.as_repos():
             artifact.repos.download_jar(artifact, 
                 cache_manager.get_jar_path(artifact))
    pool.join()

    ## append jars to path
    for artifact in artifact_set:
        sys.path.append(cache_manager.get_jar_path(artifact, filepath=True))
                 

