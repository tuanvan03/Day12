import redis
import time
from fastapi import HTTPException
from .config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def check_rate_limit(user_id: str):
    current_time = time.time()
    window_start = current_time - 60
    
    key = f"rate_limit:{user_id}"
    
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zrange(key, 0, -1)
    pipe.zadd(key, {str(current_time): current_time})
    pipe.expire(key, 60)
    results = pipe.execute()
    
    # results[1] is the output of zrange, containing the elements in the window
    current_count = len(results[1])
    max_requests = settings.RATE_LIMIT_PER_MINUTE
    
    if current_count >= max_requests:
        oldest = float(results[1][0]) if results[1] else current_time
        retry_after = int(oldest + 60 - current_time) + 1
        reset_at = int(oldest + 60)
        
        raise HTTPException(
            status_code=429, 
            detail={
                "error": "Rate limit exceeded",
                "limit": max_requests,
                "window_seconds": 60,
                "retry_after_seconds": retry_after
            },
            headers={
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_at),
                "Retry-After": str(retry_after)
            }
        )
