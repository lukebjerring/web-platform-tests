https://www.w3.org/TR/CSS2/visudet.html#line-height
// "We recommend a used value for 'normal' between 1.0 to 1.2"

[
  'sans-serif',
  'serif',
]
  .forEach(family => {
  [
    8,
    10,
    12,
    16,
    24,
    48,
    72
  ].forEach(size => {
    test(() => {
      let p = document.createElement('p');
      p.innerText = 'Some content';
      p.style.lineHeight = 'normal';
      p.style.fontFamily = family;
      p.style.fontSize = `${size}px`;
      document.body.appendChild(p);

      let computed = computeDisplayedHeight(p);
      let ratio = computed / size;
      assert_greater_than_equal(ratio, 1.0, 'line-height: \'normal\' computed height ratio');
      assert_less_than_equal(ratio, 1.2, 'line-height: \'normal\' computed height ratio');
    }, `Computed line-height: normal for ${size}px ${family}`);
  });
});

/** Get the height of the given element in pixels */
function computeDisplayedHeight(e) {
  var temp = document.createElement(e.nodeName);
  temp.setAttribute(
    "style",
    "margin:0px"
    + ";padding:0px"
    + ";font-family:"
    + e.style.fontFamily
    + ";font-size:"
    + e.style.fontSize);
  temp.innerHTML = "test";
  temp = document.body.appendChild(temp);
  var ret = temp.clientHeight;
  temp.parentNode.removeChild(temp);
  return ret;
}
