import unittest

from jip.repository import MavenFileSystemRepos
from jip.maven import Artifact
from contextlib import contextmanager
import shutil
import tempfile

import errno    
import os

@contextmanager
def tmpdir():
    dirname = tempfile.mkdtemp()
    try:
        yield dirname
    finally:
        shutil.rmtree(dirname)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

class RespositoryTests(unittest.TestCase):

    def testLocalDownloadOfPomWithUtfChars(self):
        with tmpdir() as temp_repo_dir:
            artifact_dir = "%s/dummygroup/dummyartifact/1.0.0/" % temp_repo_dir
            mkdir_p(artifact_dir)
            with open("%sdummyartifact-1.0.0.pom" % artifact_dir, "wb") as f:
                f.write("\xe2")
            testee = MavenFileSystemRepos('dummy_name', temp_repo_dir)
            artifact = Artifact('dummygroup', 'dummyartifact', '1.0.0')
            pom = testee.download_pom(artifact)
            # should not raise an UnicodeDecodeError
            pom.encode("utf-8")

if __name__ == '__main__':
    unittest.main()
