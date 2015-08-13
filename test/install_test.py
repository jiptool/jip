import unittest

from jip import repos_manager, index_manager
from jip.maven import Artifact
from jip.commands import _resolve_artifacts

class InstallTests(unittest.TestCase):
    def setUp(self):
        repos_manager.init_repos()
        index_manager.initialize()

    def testArtifact(self):
        commons_lang = Artifact('commons-lang', 'commons-lang', '2.6')
        self.assertEqual(str(commons_lang), 'commons-lang:commons-lang:2.6')
        
    def testResolve(self):
        junit = Artifact('junit', 'junit', '3.8.1')
        artifacts = _resolve_artifacts([junit])
        self.assertEqual(len(artifacts), 1)

    def testExclusion(self):
        pig = Artifact('org.apache.pig', 'pig', '0.8.3')
        exclusion = [Artifact(*x.split(":")) for x in ['ant:ant', 'junit:junit','org.eclipse.jdt:core']]
        artifacts = _resolve_artifacts([pig], exclusion)
        self.assertTrue(len(artifacts) > 0)
        self.assertFalse(any([x.is_same_artifact(Artifact('ant', 'ant')) for x in artifacts]))
        self.assertFalse(any([x.is_same_artifact(Artifact('junit', 'junit')) for x in artifacts]))
        self.assertFalse(any([x.is_same_artifact(Artifact('org.eclipse', 'core')) for x in artifacts]))


if __name__ == '__main__':
    unittest.main()
