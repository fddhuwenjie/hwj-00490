#!/usr/bin/env minibash
# Test Script 2: Loops and Conditionals

echo "=== Test: Loops and Conditionals ==="

for i in 1 2 3 4 5; do echo "Count: $i"; done

echo "--- if/else test ---"
if true; then echo "true branch works"; fi

if false; then echo "should not print"; else echo "else branch works"; fi

echo "--- while loop test ---"
n=0
while false; do echo "should not print"; done
echo "while loop skipped correctly"

echo "--- for with glob test ---"
for f in /tmp/mb_test_*.txt; do echo "Found: $f"; done

echo "--- conditional execution test ---"
true && echo "&& works with true"
false || echo "|| works with false"
false && echo "should not print"
true || echo "should not print either"

echo "--- nested if test ---"
if false; then echo "bad"; else echo "nested else ok"; fi

echo "--- exit code test ---"
true
echo "Last exit code after true: $?"

echo "=== Loops and Conditionals Tests Complete ==="
