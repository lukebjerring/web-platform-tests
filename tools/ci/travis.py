"""Helper methods and classes for invoking WPT tests for a given PR in
Travis builds."""

from __future__ import print_function
import sys

class TravisFold(object):
    """Context for TravisCI folding mechanism. Subclasses object.

    See: https://blog.travis-ci.com/2013-05-22-improving-build-visibility-log-folds/
    """

    def __init__(self, name):
        """Register TravisCI folding section name."""
        self.name = name

    def __enter__(self):
        """Emit fold start syntax."""
        print(("travis_fold:start:%s" % self.name), file=sys.stderr)

    def __exit__(self, type, value, traceback):
        """Emit fold end syntax."""
        print(("travis_fold:end:%s" % self.name), file=sys.stderr)
