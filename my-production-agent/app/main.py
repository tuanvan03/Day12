import os
import time
import json
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit, r
from .cost_guard import check_budget

INSTANCE_ID = os.getenv("INSTANCE_ID", f"instance-{uuid.uuid4().hex[:6]}")
START_TIME = time.time()

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "instance": INSTANCE_ID
        }
        return json.dumps(log_record)

logger = logging.getLogger("agent")
logger.setLevel(settings.LOG_LEVEL)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
if not logger.handlers:
    logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting instance {INSTANCE_ID}")
    yield
    logger.info(f"Instance {INSTANCE_ID} shutting down")

app = FastAPI(title="Production Agent", lifespan=lifespan)

class AskRequest(BaseModel):
    question: str
    user_id: str

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "instance_id": INSTANCE_ID, 
        "uptime_seconds": round(time.time() - START_TIME, 1)
    }

@app.get("/ready")
def ready():
    try:
        r.ping()
        return {"ready": True, "instance": INSTANCE_ID}
    except Exception as e:
        logger.error(f"Redis connection failed during ready check: {e}")
        raise HTTPException(status_code=503, detail="Redis not available")

@app.post("/ask")
def ask(
    req: AskRequest,
    _auth = Depends(verify_api_key)
):
    logger.info(f"Received question from {req.user_id}")
    
    check_rate_limit(req.user_id)
    check_budget(req.user_id)
    
    try:
        history_key = f"history:{req.user_id}"
        history = r.lrange(history_key, 0, -1)
        
        response_text = f"Agent says: I received your question: '{req.question}'"
        
        r.rpush(history_key, json.dumps({"role": "user", "content": req.question}))
        r.rpush(history_key, json.dumps({"role": "agent", "content": response_text}))
        
        r.ltrim(history_key, -20, -1)
        r.expire(history_key, 86400) # Save for 1 day
        
        return {
            "session_id": req.user_id,
            "question": req.question,
            "answer": response_text,
            "turn": (len(history) // 2) + 1,
            "served_by": INSTANCE_ID
        }
    except Exception as e:
        logger.error(f"Error processing /ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))
