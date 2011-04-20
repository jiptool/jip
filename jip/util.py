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

import urllib
import urllib2
from StringIO import StringIO

from . import JIP_VERSION

JIP_USER_AGENT = 'jip/%s' % JIP_VERSION
BUF_SIZE = 4096

class DownloadException(Exception):
    pass

def download(url, target):
    ### download file to target (target is a file-like object)
    request = urllib2.Request(url=url)
    request.add_header('User-Agent', JIP_USER_AGENT)
    try:
        source = urllib2.urlopen(request)
        buf=source.read(BUF_SIZE)
        while len(buf) > 0:
            target.write(buf)
            buf = source.read(BUF_SIZE)
        source.close()
    except urllib2.HTTPError:
        raise DownloadException()

def download_string(url):
    buf = StringIO()
    download(url, buf)
    data = buf.getvalue()
    buf.close()
    return data

