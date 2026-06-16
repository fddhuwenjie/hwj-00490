#!/usr/bin/env minibash
# Test Script: Here Document and Here String

echo "=== Test: Here Document and Here String ==="

echo "--- Basic Here Document ---"
cat << HEREDOC_EOF
Hello from Here Document
Multiple lines supported
HEREDOC_EOF

echo "--- Here Document with variable expansion ---"
NAME="MiniBash"
cat << HEREDOC_EOF
Welcome to $NAME
Version: 1.0
HEREDOC_EOF

echo "--- Here Document with quoted delimiter (no expansion) ---"
NAME="MiniBash"
cat << 'HEREDOC_EOF'
No expansion: $NAME stays literal
HEREDOC_EOF

echo "--- Here String test ---"
cat <<< "Hello from Here String"

echo "--- Here String with variable ---"
MSG="variable content"
cat <<< $MSG

echo "=== Here Document and Here String Tests Complete ==="
