    git checkout idl-file-updates-reffyreports-aggregated
    while read idl; do
      git checkout origin/idl-file-updates-$idl -- interfaces/$idl.idl
    done <trivial.txt
    git reset master
    git --no-pager diff --name-only
