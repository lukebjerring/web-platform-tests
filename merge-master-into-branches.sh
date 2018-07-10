    set -e
    while read idl; do
      git checkout idl-file-updates-$idl
      git merge master --no-edit
    done <branches.txt
