    while read idl; do
      git diff -s --exit-code master..origin/idl-file-updates-$idl -- interfaces/$idl.idl || {
        DIFF=$(git --no-pager diff -U0 -w -B master..origin/idl-file-updates-$idl -- interfaces/$idl.idl)
        CHANGED_LINES=$(echo "$DIFF" | grep '^[+-]' | grep -Ev '^(--- a/|\+\+\+ b/)')
        NOT_BLANK_OR_COMMENTS=$(echo "$CHANGED_LINES" | grep -Ev '^[+-](//.*)?$')
        if [[ "$NOT_BLANK_OR_COMMENTS" == "" ]]
        then
          echo $idl
        fi
      }
    done <changed.txt
