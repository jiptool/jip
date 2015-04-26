#!/usr/bin/env python
"""Run unittests in this."""

import os
import pkgutil
import sys
import unittest

def suite() :
    loader = unittest.defaultTestLoader
    if len(sys.argv) > 1:
        names = sys.argv[1:]
        test_suite = loader.loadTestsFromNames(names)
    else:
        pkgpath = os.path.dirname(__file__)
        names = [name for _, name,
                 _ in pkgutil.iter_modules([pkgpath])]
        test_suite = loader.loadTestsFromNames(names)
    return test_suite

def main():
    runner = unittest.TextTestRunner()
    result = runner.run(suite())
    if result.wasSuccessful():
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
