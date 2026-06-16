#!/usr/bin/env minibash
# Test Script: Aliases and Type Command

echo "=== Test: Aliases and Type Command ==="

echo "--- Define aliases ---"
alias ll='ls -la'
alias la='ls -a'
alias ..='cd ..'
alias cls='clear'
alias greet='echo Hello'

echo "--- List all aliases ---"
alias

echo "--- Use alias ---"
greet

echo "--- Type command for builtins ---"
type echo
type cd
type exit

echo "--- Type command for aliases ---"
type ll
type greet

echo "--- Type command for unknown ---"
type nonexistent_command_xyz

echo "--- Unalias test ---"
unalias greet
type greet

echo "--- Nested alias expansion test ---"
alias cmd1='echo nested'
alias cmd2='cmd1 expansion'
cmd2

echo "=== Aliases and Type Command Tests Complete ==="
