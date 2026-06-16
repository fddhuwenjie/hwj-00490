#!/usr/bin/env minibash
# Test Script 3: Functions and Variables

echo "=== Test: Functions and Variables ==="

greeting() { echo "Hello, $1!"; }
greeting "World"
greeting "MiniBash"

add_prefix() { echo "[PREFIX] $1"; }
add_prefix "test message"

name="MiniBash"
version="1.0"
echo "Name: $name, Version: ${version}"

export MY_VAR="from_script"
echo "Exported: $MY_VAR"

unset MY_VAR
echo "After unset MY_VAR is empty: '$MY_VAR'"

echo "Home: $HOME"
echo "User: $USER"
echo "Path starts: $(echo $PATH | cut -c1-20)"

echo "Command sub: $(echo hello)"
echo "Nested: $(echo $(echo deep))"

count_args() { echo "Args: $#"; }
count_args a b c
count_args

echo "Exit code check: $?"

echo "=== Functions and Variables Tests Complete ==="
