// We have to set the url here to ensure we get the same escaping as in the harness
// and also to handle the case where the test changes the fragment
window.__wptrunner_url = "%(url)s";
(function(__wptrunner_callback) {
  window.__wptrunner_testdriver_callback = __wptrunner_callback;
  window.__wptrunner_process_next_event();
})(arguments[arguments.length - 1]);
