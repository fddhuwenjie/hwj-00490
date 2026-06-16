#!/usr/bin/env minibash
# Test Script: Arithmetic and Test Expressions

echo "=== Test: Arithmetic and Test Expressions ==="

echo "--- Basic arithmetic ---"
echo "2 + 3 = $((2 + 3))"
echo "10 - 4 = $((10 - 4))"
echo "3 * 7 = $((3 * 7))"
echo "20 / 4 = $((20 / 4))"
echo "17 % 5 = $((17 % 5))"

echo "--- Parentheses for precedence ---"
echo "2 + 3 * 4 = $((2 + 3 * 4))"
echo "(2 + 3) * 4 = $(( (2 + 3) * 4 ))"

echo "--- Variable in arithmetic ---"
x=10
y=3
echo "x=$x, y=$y"
echo "x + y = $((x + y))"
echo "x * y = $((x * y))"
echo "x - y = $((x - y))"

echo "--- Double bracket string comparison ---"
if [[ "hello" == "hello" ]]; then echo "string == works"; fi
if [[ "hello" != "world" ]]; then echo "string != works"; fi

echo "--- Double bracket integer comparison ---"
a=5
b=10
if [[ $a -lt $b ]]; then echo "$a < $b works"; fi
if [[ $b -gt $a ]]; then echo "$b > $a works"; fi
if [[ $a -le 5 ]]; then echo "$a <= 5 works"; fi
if [[ $b -ge 10 ]]; then echo "$b >= 10 works"; fi
if [[ $a -eq 5 ]]; then echo "$a == 5 works (-eq)"; fi
if [[ $a -ne $b ]]; then echo "$a != $b works (-ne)"; fi

echo "--- Double bracket file test ---"
if [[ -f /tmp ]]; then echo "should not print"; else echo "-f /tmp correctly false (it is a dir)"; fi
if [[ -d /tmp ]]; then echo "-d /tmp works (it is a dir)"; fi
if [[ -e /tmp ]]; then echo "-e /tmp works (exists)"; fi

echo "--- Double bracket logical operators ---"
if [[ "yes" == "yes" ]] && [[ 1 -lt 2 ]]; then echo "&& in condition works"; fi
if [[ "no" == "yes" ]] || [[ 1 -lt 2 ]]; then echo "|| in condition works"; fi

echo "--- Arithmetic in while loop ---"
count=0
result=""
while [[ $count -lt 5 ]]; do
    result="$result$count"
    count=$((count + 1))
done
echo "Counted: $result"

echo "=== Arithmetic and Test Expressions Tests Complete ==="
