import unittest

from jip import repos_manager, index_manager
from jip.maven import Artifact
from jip.commands import _resolve_artifacts

class InstallTests(unittest.TestCase):
    def setUp(self):
        repos_manager.init_repos()
        index_manager.initialize()

    def testResolve(self):
        commons_lang = Artifact('commons-lang', 'commons-lang', '2.6')
        print commons_lang
        artifacts = _resolve_artifacts([commons_lang])
        print artifacts
        self.assert_(len(artifacts) == 1)

    def testExclusion(self):
        pig = Artifact('org.apache.pig', 'pig', '0.8.3')
        exclusion = map(lambda x: Artifact(*x.split(":")), ['ant:ant', 'junit:junit','org.eclipse.jdt:core'])
        print exclusion
        artifacts = _resolve_artifacts([pig], exclusion)
        print artifacts
        self.assert_(len(artifacts) > 0)
        self.assert_(not any(map(lambda x: x.is_same_artifact(Artifact('ant', 'ant')), artifacts)))
        self.assert_(not any(map(lambda x: x.is_same_artifact(Artifact('junit', 'junit')), artifacts)))
        self.assert_(not any(map(lambda x: x.is_same_artifact(Artifact('org.eclipse', 'core')), artifacts)))


if __name__ == '__main__':
    unittest.main()

