#!/usr/bin/env minibash
# Test Script 1: Pipes and Redirections

echo "=== Test: Pipes and Redirections ==="

echo "Hello from minibash" > /tmp/mb_test_output.txt
echo "Content written to file"
cat /tmp/mb_test_output.txt

echo "Appended line" >> /tmp/mb_test_output.txt
echo "Content after append:"
cat /tmp/mb_test_output.txt

echo "pipe input" | cat
echo "pipe test passed"

echo "three" | cat | cat
echo "multi-pipe test passed"

echo "stderr test message" 2> /tmp/mb_test_stderr.txt
echo "stderr redirect test passed"

echo "combined redirect test" &> /tmp/mb_test_combined.txt
cat /tmp/mb_test_combined.txt

echo "Hello World" | cat > /tmp/mb_test_pipe_redir.txt
cat /tmp/mb_test_pipe_redir.txt

echo "=== Pipes and Redirections Tests Complete ==="
