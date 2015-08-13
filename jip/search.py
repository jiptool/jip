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
    import urllib.parse as urlparse
except ImportError:
    import urllib as urlparse
try: import simplejson as json
except ImportError: import json
from jip.util import download_string

class SearchProvider(object):
    def search(self, query, maxresults=20):
        """ Search and return list of tuple(groupId, artifactId, version, packaging)"""
        pass

    def search_group_artifact(self, group, artifact, maxresults=20):
        """ Search with group and artifact name"""
        pass

class SonatypeMavenSearch(SearchProvider):
    query_service = "http://search.maven.org/solrsearch/select?q=%s&rows=%d&wt=json"
    def search(self, query, maxresults=20):
        query_url = self.query_service % (urlparse.quote(query), maxresults)

        data = download_string(query_url)
        
        return self._parse_results(data, version_name='latestVersion') 

    def search_group_artifact(self, group, artifact, maxresults=20):
        query = 'g:"%s" AND a:"%s"'%(group, artifact)
        query_url = self.query_service % (urlparse.quote(query), maxresults)
        query_url += "&core=gav"

        data = download_string(query_url)
        return self._parse_results(data, version_name='v')

    def _parse_results(self, data, version_name):
        results = json.loads(data)
       
        docs = results['response']['docs']
        return [(doc['g'], doc['a'], doc[version_name], doc['p']) for doc in docs]

searcher = SonatypeMavenSearch()

