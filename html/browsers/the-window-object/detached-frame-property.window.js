const detachedWindow = document.createElement('iframe');
detachedWindow.src = 'about:blank';
document.body.appendChild(detachedWindow);
document.body.removeChild(detachedWindow);

test(() => {
  assert_true(!!detachedWindow.postMessage);
}, "detachedWindow.postMessage is defined");
test(() => {
  assert_true(!!detachedWindow.close);
}, "detachedWindow.close is defined");
test(() => {
  assert_true(!!detachedWindow.locationbar);
}, "detachedWindow.locationbar is defined");
test(() => {
  assert_true(!!detachedWindow.history);
}, "detachedWindow.history is defined");
test(() => {
  assert_true(!!detachedWindow.screen);
}, "detachedWindow.screen is defined");
test(() => {
  assert_true(!!detachedWindow.location);
}, "detachedWindon.location is defined");
test(() => {
  assert_true(detachedWindow.closed);
}, "detachedWindow.closed is true");
test(() => {
  assert_equals(detachedWindow.top, null);
}, "detachedWindow.top is null");
test(() => {
  assert_equals(detachedWindow.opener, null);
}, "detachedWindow.opener is null");
test(() => {
  assert_equals(detachedWindow.parent, null);
}, "detachedWindow.parent is null");
test(() => {
  assert_equals(detachedWindow.frameElement, null);
}, "detachedWindow.frameElement is null");
test(() => {
  assert_equals(detachedWindow.window, null);
}, "detachedWindow.window is null");
test(() => {
  assert_equals(detachedWindow.frames, null);
}, "detachedWindow.frames is null");
test(() => {
  assert_equals(detachedWindow.self, null);
}, "detachedWindow.self is null");
test(() => {
  assert_true(!detachedWindow.localStorage);
}, "detachedWindow.localStorage is undefined");
test(() => {
  assert_true(!!detachedWindow.document);
}, "detachedWindow.document is defined");
test(() => {
  assert_true(!!detachedWindow.XMLHttpRequest);
}, "detachedWindow.XMLHttpRequest is defined");
test(() => {
  assert_true(!!detachedWindow.getComputedStyle);
}, "detachedWindow.getComputedStyle is defined");
test(() => {
  assert_equals(detachedWindow.innerHeight, 0);
}, "detachedWindow.innerHeight is 0");
test(() => {
  assert_equals(detachedWindow.innerWidth, 0);
}, "detachedWindow.innerWidth is 0");