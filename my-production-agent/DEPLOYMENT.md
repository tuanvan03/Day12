# Deployment Guide (Railway)

## Overview
This production AI agent is fully ready to be deployed as stateless containers connected to a Redis instance.
Run test.sh to test the agent locally.

curl http://localhost/health
{"status":"ok","instance_id":"instance-dcd788","uptime_seconds":120.6}

curl -s http://localhost/readylhost/ready
{"ready":true,"instance":"instance-ce219c"}

curl -s -X POST http://localhost/ask \
  -H "X-API-Key: secret" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
{"session_id":"user1","question":"Hello","answer":"Agent says: I received your question: 'Hello'","turn":1,"served_by":"instance-c7947b"}


## Deploying to Railway


## Deploying to Render

