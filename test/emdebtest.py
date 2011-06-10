import unittest

from jip.embed import require

class JipRequireTests(unittest.TestCase):
    def testRequire(self):
        require("commons-lang:commons-lang:2.6")
        from org.apache.commons.lang import StringUtils

        self.assertEquals(StringUtils.removeStart("jip rocks", "jip"), " rocks")
        self.assertEquals(StringUtils.reverse("jip rocks"), "skcor pij")

if __name__ == '__main__':
    unittest.main()

