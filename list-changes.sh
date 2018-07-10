    while read idl; do
      DIFF=$(git --no-pager diff master..idl-file-updates-$idl -- interfaces/$idl.idl)
      if [[ "$DIFF" != "" ]]
      then
        echo $idl
        git diff --stat master..idl-file-updates-$idl
      fi
    done <changed.txt
