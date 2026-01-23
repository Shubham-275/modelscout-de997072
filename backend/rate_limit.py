"""
Rate limiting configuration for ModelScout API.

Prevents abuse and DoS attacks by limiting request rates.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask
import os


def init_rate_limiter(app: Flask) -> Limiter:
    """
    Initialize rate limiter for the Flask app.
    
    Default limits:
    - Global: 200 requests per day, 50 per hour
    - Search endpoint: 10 per minute (expensive Mino API calls)
    - Compare endpoint: 5 per minute (very expensive)
    - Other endpoints: 30 per minute
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Limiter instance
    """
    # Use Redis in production for distributed rate limiting
    # Use in-memory storage for development
    storage_uri = os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://")
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=storage_uri,
        strategy="fixed-window",  # Can be changed to "moving-window" for smoother limiting
        headers_enabled=True,  # Add rate limit headers to responses
    )
    
    return limiter


# Rate limit decorators for different endpoint types
SEARCH_LIMIT = "10 per minute"  # Expensive Mino API calls
COMPARE_LIMIT = "5 per minute"  # Very expensive (2x Mino calls)
STANDARD_LIMIT = "30 per minute"  # Standard endpoints
ANALYST_LIMIT = "20 per minute"  # AI analyst endpoints
