import logging
from fastapi import HTTPException
from .config import settings
from .rate_limiter import r

logger = logging.getLogger("agent")

def check_budget(user_id: str):
    user_key = f"budget:{user_id}"
    global_key = "budget:global_total"
    
    user_spend = r.get(user_key)
    global_spend = r.get(global_key)
    
    # Enforce strictly 10$/month per user as per requirements
    user_limit = settings.MONTHLY_BUDGET_USD
    
    if user_spend and float(user_spend) >= user_limit:
        raise HTTPException(
            status_code=402, 
            detail={
                "error": "Payment Required: Individual user budget exceeded",
                "used_usd": float(user_spend),
                "budget_usd": user_limit
            }
        )
    
    # Mock increment budget by a small LLM call cost
    cost = 0.05
    new_user_spend = float(r.incrbyfloat(user_key, cost))
    
    if new_user_spend >= user_limit * 0.8:
         logger.warning(f"User {user_id} at {new_user_spend/user_limit*100:.0f}% of budget")
