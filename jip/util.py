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

import urllib
import urllib2
import time
from StringIO import StringIO
import Queue
import threading

from . import JIP_VERSION, logger

JIP_USER_AGENT = 'jip/%s' % JIP_VERSION
BUF_SIZE = 4096

class DownloadException(Exception):
    pass

def download(url, target, async=False, close_target=False, quiet=True):
    ### download file to target (target is a file-like object)
    if async:
        pool.submit(url, target)
    else:
        request = urllib2.Request(url=url)
        request.add_header('User-Agent', JIP_USER_AGENT)
        try:
            t0 = time.time()
            source = urllib2.urlopen(request)
            size = source.headers.getheader('Content-Length')
            if not quiet:
                logger.info('[Downloading] %s %s bytes to download' % (url, size))
            buf=source.read(BUF_SIZE)
            while len(buf) > 0:
                target.write(buf)
                buf = source.read(BUF_SIZE)
            source.close()
            if close_target:
                target.close()
            t1 = time.time()
            if not quiet:
                logger.info('[Downloading] Download %s completed in %f secs' % (url, (t1-t0)))
        except urllib2.HTTPError:
            raise DownloadException()
        except urllib2.URLError:
            raise DownloadException()

def download_string(url):
    buf = StringIO()
    download(url, buf)
    data = buf.getvalue()
    buf.close()
    return data

class DownloadThreadPool(object):
    def __init__(self, size=3):
        self.queue = Queue.Queue()
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
        logger.warn('Warning: no virtualenv detected, remember to activate it.')
        if 'JYTHON_HOME' in os.environ:
            JYTHON_HOME = os.environ['JYTHON_HOME']
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

