import json
import re

drafts_csswg_re = re.compile(r"https?\:\/\/drafts\.csswg\.org\/([^/?#]+)")
w3c_tr_re = re.compile(r"https?\:\/\/www\.w3c?\.org\/TR\/([^/?#]+)")
w3c_dev_re = re.compile(r"https?\:\/\/dev\.w3c?\.org\/[^/?#]+\/([^/?#]+)")
with file('./spec.json') as spec:
  foo = json.load(spec)
  matches = []
  misses = []
  for f in foo:
    match = None
    for r in [drafts_csswg_re, w3c_dev_re, w3c_tr_re]:
      match = match or r.match(f['href'])
    if match:
      matches.append(f['href'])
    else:
      misses.append(f['href'])
  print('Matches\n:')
  for m in matches:
    print(m)
  print('\nMisses:\n')
  for m in misses:
    print(m)
