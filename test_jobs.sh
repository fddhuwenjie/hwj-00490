#!/usr/bin/env minibash
# Test Script: Job Control and Background Execution

echo "=== Test: Job Control and Background Execution ==="

echo "--- Background execution test ---"
sleep 0.1 &
echo "Launched sleep in background, PID=$!"

echo "--- Multiple background jobs ---"
sleep 0.2 &
sleep 0.3 &
echo "Launched two more background jobs"

echo "--- Jobs listing test ---"
jobs

echo "--- Wait for all background jobs ---"
wait
echo "All background jobs completed"

echo "--- $! variable test ---"
sleep 0.1 &
LAST_PID=$!
echo "Last background PID: $LAST_PID"
wait

echo "--- Foreground execution test ---"
echo "This runs in foreground"

echo "=== Job Control Tests Complete ==="
