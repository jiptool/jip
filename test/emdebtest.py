import sys
import unittest

from jip.embed import require

def is_jython():
    return sys.platform.lower().startswith('java')

class JipRequireTests(unittest.TestCase):
    def testRequire(self):
        if is_jython():
            return
        require("commons-lang:commons-lang:2.6")
        from org.apache.commons.lang import StringUtils

        self.assertEquals(StringUtils.removeStart("jip rocks", "jip"), " rocks")
        self.assertEquals(StringUtils.reverse("jip rocks"), "skcor pij")

if __name__ == '__main__':
    unittest.main()
