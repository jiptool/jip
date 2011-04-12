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
import simplejson as json

class SearchProvider(object):
    def search(self, query, maxresults=20):
        """ Search and return list of tuple(groupId, artifactId, version, packaging)"""
        pass

class SonatypeMavenSearch(SearchProvider):
    query_service = "http://search.maven.org/solrsearch/select?q=%s&rows=%d&wt=json"
    def search(self, query, maxresults=20):
        query_url = self.query_service % (query, maxresults)

        s = urllib.urlopen(query_url)
        data = s.read()
        s.close()
        
        return self.parse_results(data)

    def parse_results(self, data):
        results = json.loads(data)
       
        docs = results['response']['docs']
        return [(doc['g'], doc['a'], doc['latestVersion'], doc['p']) for doc in docs]

searcher = SonatypeMavenSearch()

