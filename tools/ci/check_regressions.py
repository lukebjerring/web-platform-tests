#!/usr/bin/env python

import argparse
import certifi
import json
import logging
import os
import sys
import urllib3

from ConfigParser import SafeConfigParser
from mozlog.formatters import JSONFormatter, TbplFormatter
from mozlog.handlers import BaseHandler, LogLevelFilter, StreamHandler
from urllib import urlencode

here = os.path.dirname(__file__)
wpt_root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(wpt_root, "wptrunner"))
sys.path.insert(0, wpt_root)

import state
import tools.wpt.run

from tools.wpt.utils import Kwargs
from tools.wpt import markdown
from travis import TravisFold
from wptrunner import wptrunner
from wptrunner.formatters import WptreportFormatter

logger = None

def main():  # type: () -> int
    """Perform check_stability functionality and return exit code."""
    venv = state.setup_venv()
    args, wpt_args = get_parser().parse_known_args()
    return run(venv, wpt_args, **vars(args))

def get_parser():  # type: () -> argparse.Namespace
    """Create and return script-specific argument parser."""
    description = """Detect regressions in new/changed tests by executing tests
    and comparing results to the tests last production execution."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--user",
                        action="store",
                        # Travis docs say do not depend on USER env variable.
                        # This is a workaround to get what should be the same value
                        default=os.environ.get("TRAVIS_REPO_SLUG", "w3c").split('/')[0],
                        help="Travis user name")
    parser.add_argument("--output-bytes",
                        action="store",
                        type=int,
                        help="Maximum number of bytes to write to standard output/error")
    parser.add_argument("--metadata",
                        dest="metadata_root",
                        action="store",
                        default=wpt_root,
                        help="Directory that will contain MANIFEST.json")
    parser.add_argument("--config-file",
                        action="store",
                        type=str,
                        help="Location of ini-formatted configuration file",
                        default="check_stability.ini")
    parser.add_argument("--rev",
                        action="store",
                        default=None,
                        help="Commit range to use")
    return parser

def setup_logging():
    """Set up basic debug logger."""
    global logger
    logger = logging.getLogger(here)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(logging.BASIC_FORMAT, None)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def set_default_args(kwargs):
    kwargs.set_if_none("sauce_platform",
                       os.environ.get("PLATFORM"))
    kwargs.set_if_none("sauce_build",
                       os.environ.get("TRAVIS_BUILD_NUMBER"))
    python_version = os.environ.get("TRAVIS_PYTHON_VERSION")
    kwargs.set_if_none("sauce_tags",
                       [python_version] if python_version else [])
    kwargs.set_if_none("sauce_tunnel_id",
                       os.environ.get("TRAVIS_JOB_NUMBER"))
    kwargs.set_if_none("sauce_user",
                       os.environ.get("SAUCE_USERNAME"))
    kwargs.set_if_none("sauce_key",
                       os.environ.get("SAUCE_ACCESS_KEY"))


def run(venv, wpt_args, **kwargs):
    global logger

    retcode = 0
    parser = get_parser()

    wpt_args = tools.wpt.run.create_parser().parse_args(wpt_args)

    with open(kwargs["config_file"], 'r') as config_fp:
        config = SafeConfigParser()
        config.readfp(config_fp)
        skip_tests = config.get("file detection", "skip_tests").split()
        ignore_changes = set(config.get("file detection", "ignore_changes").split())
        results_url = config.get("file detection", "results_url")

    if kwargs["output_bytes"] is not None:
        replace_streams(kwargs["output_bytes"],
                        "Log reached capacity (%s bytes); output disabled." % kwargs["output_bytes"])


    wpt_args.metadata_root = kwargs["metadata_root"]
    try:
        os.makedirs(wpt_args.metadata_root)
    except OSError:
        pass

    setup_logging()

    browser_name = wpt_args.product.split(":")[0]

    if browser_name == "sauce" and not wpt_args.sauce_key:
        logger.warning("Cannot run tests on Sauce Labs. No access key.")
        return retcode

    pr_number = state.pr()

    with TravisFold("browser_setup"):
        logger.info(markdown.format_comment_title(wpt_args.product))

        if state.pr is not None:
            state.deepen_checkout(kwargs["user"])

        # Ensure we have a branch called "master"
        state.fetch_wpt(kwargs["user"], "master:master")

        head_sha1 = state.get_sha1()
        logger.info("Testing web-platform-tests at revision %s" % head_sha1)

        wpt_kwargs = Kwargs(vars(wpt_args))

        if not wpt_kwargs["test_list"]:
            manifest_path = os.path.join(wpt_kwargs["metadata_root"], "MANIFEST.json")
            tests_changed, files_affected = state.get_changed_files(
                manifest_path, kwargs["rev"],
                ignore_changes, skip_tests)

            if not (tests_changed or files_affected):
                logger.info("No tests changed")
                return 0

            if tests_changed:
                logger.debug("Tests changed:\n%s" % "".join(" * %s\n" % item for item in tests_changed))

            if files_affected:
                logger.debug("Affected tests:\n%s" % "".join(" * %s\n" % item for item in files_affected))

            wpt_kwargs["test_list"] = list(tests_changed | files_affected)

        set_default_args(wpt_kwargs)

        wpt_kwargs["prompt"] = False
        wpt_kwargs["install_browser"] = True
        wpt_kwargs["install"] = wpt_kwargs["product"].split(":")[0] == "firefox"

        wpt_kwargs = tools.wpt.run.setup_wptrunner(venv, **wpt_kwargs)

        logger.info("Using binary %s" % wpt_kwargs["binary"])


    report = None
    with TravisFold("running_tests"):
        logger.info("Starting tests")

        wpt_kwargs["pause_after_test"] = False

        tbpl = StreamHandler(sys.stdout, TbplFormatter())
        handler = LogActionFilter(
            LogLevelFilter(tbpl, "WARNING"),
            ["log", "process_output"])

        # There is a public API for this in the next mozlog
        mozlogger = wptrunner.logger
        initial_handlers = mozlogger._state.handlers
        mozlogger._state.handlers = []

        report_log = "report.log"
        with open(report_log, "wb") as log:
            # Setup logging for wptrunner that keeps process output and
            # warning+ level logs only
            mozlogger.add_handler(handler)
            mozlogger.add_handler(StreamHandler(log, WptreportFormatter()))

            wptrunner.run_tests(**wpt_kwargs)

        mozlogger._state.handlers = initial_handlers

        with open(report_log, "rb") as log:
            report = json.load(log)

    if report_log:
        with TravisFold("diffing_results"):
            summary = report_to_summary(report)
            logger.debug("Results summary:")
            logger.debug(json.dumps(summary))

            result = diff(summary, wpt_kwargs['product'])
            if result is not None and len(result) < 1:
                logger.info("No regressions.")
            else:
                logger.warning("Regression(s) detected.")
                for k in result.iterkeys():
                    logger.info("%s had %d differences out of %d tests."
                                % (k, result[k][0], result[k][1]))


    else:
        logger.info("No tests run.")

    return retcode


def diff(results, product):  # type: (dict, str) -> dict
    '''Fetch a python object representing the differences in run results JSON
    for the given results. '''

    global logger

    pool = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())

    # type: (str, str) -> dict
    # Note that the dict's keys are the test paths, and values are an
    # array of [pass_count, total_test_count].
    # For example JSON output, see https://wpt.fyi/results?platform=chrome

    encodedArgs = urlencode({
        'before': ('%s@latest' % product),
        'filter': 'C'  # Changes
    })
    url = 'https://20171213t152016-dot-wptdashboard.appspot.com/api/diff?' + \
          encodedArgs
    # url = 'http://wpt.fyi/api/diff?' + encodedArgs

    body = json.dumps(results).encode('utf-8')
    headers = {
        'Content-type': 'application/json',
    }
    logger.debug("Fetching %s" % url)
    try:
        response = pool.request('POST', url, body=body, headers=headers)
    except urllib3.exceptions.SSLError as e:
        logger.warning('SSL error fetching %s: %s' % (url, e.message))
        return None

    if response.status != 200:
        logger.warning('Failed to fetch %s (%d):\n%s'
                       % (url, response.status, response.data.decode('utf-8')))
        return None

    logger.debug('Processing JSON from %s' % (url))
    response_body = response.data.decode('utf-8')
    logger.debug(response_body)
    return json.loads(response_body)


def report_to_summary(wpt_report):
    test_files = {}

    for result in wpt_report['results']:
        test_file = result['test']
        assert test_file not in test_files, (
            'Assumption that each test_file only shows up once broken!')

        if result['status'] in ('OK', 'PASS'):
            test_files[test_file] = [1, 1]
        else:
            test_files[test_file] = [0, 1]

        for subtest in result['subtests']:
            if subtest['status'] == 'PASS':
                test_files[test_file][0] += 1

            test_files[test_file][1] += 1

    return test_files


class LogActionFilter(BaseHandler):

    """Handler that filters out messages not of a given set of actions.

    Subclasses BaseHandler.

    :param inner: Handler to use for messages that pass this filter
    :param actions: List of actions for which to fire the handler
    """

    def __init__(self, inner, actions):
        """Extend BaseHandler and set inner and actions props on self."""
        BaseHandler.__init__(self, inner)
        self.inner = inner
        self.actions = actions

    def __call__(self, item):
        """Invoke handler if action is in list passed as constructor param."""
        if item["action"] in self.actions:
            return self.inner(item)


if __name__ == "__main__":
    try:
        retcode = main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
    else:
        sys.exit(retcode)
