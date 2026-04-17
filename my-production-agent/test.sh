#!/bin/bash
echo "Testing /health..."
curl -s http://localhost/health
echo -e "\n"

echo "Testing /ready..."
curl -s http://localhost/ready
echo -e "\n"

echo "Testing /ask..."
curl -s -X POST http://localhost/ask \
  -H "X-API-Key: secret" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
echo -e "\n"
