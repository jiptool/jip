import unittest

from jip.search import SonatypeMavenSearch

class SonatypeMavenSearchTests(unittest.TestCase):
    def setUp(self):
        self.searcher = SonatypeMavenSearch()

    def testGenericSearch(self):
        query = "commons-lang"
        results =self.searcher.search(query)
        self.assertTrue(results is not None)
        self.assertTrue(len(results) > 0)
        self.assertTrue(results[0][0] is not None)
        self.assertTrue(results[0][1] is not None)
        self.assertTrue(results[0][2] is not None)
        self.assertTrue(results[0][3] is not None)

    def testGroupAndArtifactSearch(self):
        group = "commons-lang"
        artif = "commons-lang"
        results =self.searcher.search_group_artifact(group, artif)
        self.assertTrue(results is not None)
        self.assertTrue(len(results) > 0)
        self.assertEquals(results[0][0], group)
        self.assertEquals(results[0][1], group)
        self.assertTrue(results[0][2] is not None)
        self.assertTrue(results[0][3] is not None)

if __name__ == '__main__':
    unittest.main()
