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

import time
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO
try:
    import queue
except ImportError:
    import Queue as queue
import threading

from jip import JIP_VERSION, logger

JIP_USER_AGENT = 'jip/%s' % JIP_VERSION
BUF_SIZE = 4096

class DownloadException(Exception):
    pass

def download(url, target, async=False, close_target=False, quiet=True):
    import requests
    ### download file to target (target is a file-like object)
    if async:
        pool.submit(url, target)
    else:
        try:
            t0 = time.time()
            source = requests.get(url, headers={ 'User-Agent': JIP_USER_AGENT})
            size = source.headers['Content-Length']
            if not quiet:
                logger.info('[Downloading] %s %s bytes to download' % (url, size))
            for buf in source.iter_content(BUF_SIZE):
                target.write(buf)
            source.close()
            if close_target:
                target.close()
            t1 = time.time()
            if not quiet:
                logger.info('[Downloading] Download %s completed in %f secs' % (url, (t1-t0)))
        except requests.exceptions.RequestException:
            _, e, _ = sys.exc_info()
            raise DownloadException(url, e)

def download_string(url):
    import requests
    response = requests.get(url, headers={ 'User-Agent': JIP_USER_AGENT})
    if response.status_code == 200:
        data = response.text
        response.close()
        return data
    else:
        return False

class DownloadThreadPool(object):
    def __init__(self, size=3):
        self.queue = queue.Queue()
        self.workers = [threading.Thread(target=self._do_work) for _ in range(size)]
        self.initialized = False

    def init_threads(self):
        for worker in self.workers:
            worker.setDaemon(True)
            worker.start()
        self.initialized = True

    def _do_work(self):
        while True:
            url, target = self.queue.get()
            download(url, target, close_target=True, quiet=False)
            self.queue.task_done()

    def join(self):
        self.queue.join()

    def submit(self, url, target):
        if not self.initialized:
            self.init_threads()
        self.queue.put((url, target))

pool = DownloadThreadPool(3)

def get_virtual_home():
    if 'VIRTUAL_ENV' in os.environ:
        JYTHON_HOME = os.environ['VIRTUAL_ENV']
    else:
        ## fail back to use current directory
        JYTHON_HOME = os.getcwd()
    return JYTHON_HOME

def get_lib_path():
    JYTHON_HOME = get_virtual_home()
    DEFAULT_JAVA_LIB_PATH = os.path.join(JYTHON_HOME, 'javalib')

    if not os.path.exists(DEFAULT_JAVA_LIB_PATH):
        os.mkdir(DEFAULT_JAVA_LIB_PATH)
    return DEFAULT_JAVA_LIB_PATH
