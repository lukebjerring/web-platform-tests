"""Helper methods and classes for manipulating and querying repo state
for a given PR in Travis builds."""

import os
import sys
from typing import Set, Tuple

here = os.path.dirname(__file__)
wpt_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
sys.path.insert(0, wpt_root)

from tools.wpt import testfiles # noqa
from tools.wpt.testfiles import get_git_cmd # noqa
from tools.wpt.virtualenv import Virtualenv


def setup_venv():  # type: () -> Virtualenv
    venv = Virtualenv(os.environ.get("VIRTUAL_ENV", os.path.join(wpt_root, "_venv")))
    venv.install_requirements(os.path.join(wpt_root, "tools", "wptrunner", "requirements.txt"))
    venv.install("requests")
    return venv

def fetch_wpt(user, *args):
    git = get_git_cmd(wpt_root)
    git("fetch", "https://github.com/%s/web-platform-tests.git" % user, *args)


def get_sha1():  # type: () -> str
    """ Get and return sha1 of current git branch HEAD commit."""
    git = get_git_cmd(wpt_root)
    return git("rev-parse", "HEAD").strip()


def deepen_checkout(user):
    """Convert from a shallow checkout to a full one"""
    fetch_args = [user, "+refs/heads/*:refs/remotes/origin/*"]
    if os.path.exists(os.path.join(wpt_root, ".git", "shallow")):
        fetch_args.insert(1, "--unshallow")
    fetch_wpt(*fetch_args)


def pr():  # type: () -> str
    pr = os.environ.get("TRAVIS_PULL_REQUEST", "false")
    return pr if pr != "false" else None


def get_changed_files(manifest_path,   # type: str
                      rev,             # type: str
                      ignore_changes,  # type: bool
                      skip_tests       # type: bool
                      ):
    # type: (...) -> Tuple[Set[str], Set[str]]

    if not rev:
        branch_point = testfiles.branch_point()
        revish = "%s..HEAD" % branch_point
    else:
        revish = rev

    files_changed, files_ignored = testfiles.files_changed(revish, ignore_changes)

    if files_ignored:
        logger.info("Ignoring %s changed files:\n%s" %
                    (len(files_ignored), "".join(" * %s\n" % item for item in files_ignored)))

    tests_changed, files_affected = testfiles.affected_testfiles(files_changed, skip_tests,
                                                                 manifest_path=manifest_path)

    return tests_changed, files_affected
