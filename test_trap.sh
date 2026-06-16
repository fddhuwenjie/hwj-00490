#!/usr/bin/env minibash
# Test Script: Signal Handling and trap

echo "=== Test: Signal Handling and trap ==="

echo "--- EXIT trap test ---"
trap 'echo "EXIT trap fired: cleanup done"' EXIT
echo "EXIT trap set"

echo "--- ERR trap test ---"
trap 'echo "ERR trap fired: a command failed"' ERR
false
echo "After false command"

echo "--- List traps ---"
trap

echo "--- Remove EXIT trap ---"
trap - EXIT
echo "EXIT trap removed"

echo "--- Reset ERR trap ---"
trap - ERR

echo "--- EXIT trap with temp file ---"
TMPFILE=/tmp/minibash_trap_test_$$.txt
echo "temp data" > $TMPFILE
trap 'echo "Cleaning up temp file"; rm -f /tmp/minibash_trap_test_$$.txt' EXIT
echo "Temp file created: $TMPFILE"
cat $TMPFILE

echo "--- Ignore signal test ---"
trap '' INT
echo "INT signal now ignored"
trap - INT

echo "=== Signal Handling and trap Tests Complete ==="
