import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class UserContext(BaseModel):
    """
    Decoded user credentials containing the security boundary parameters.
    """
    scope: str
    role: str
    user_id: Optional[str] = None

class TokenManager:
    """
    Helper manager to encode and decode JSON Web Tokens for client chatbot portals.
    """
    @staticmethod
    def generate_token(scope: str, role: str, user_id: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
        """
        Generates a signed JWT with the specified scope, role, and expiration.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Multi-year token for chatbot API clients by default
            expire = datetime.now(timezone.utc) + timedelta(days=365 * 5)
            
        payload = {
            "scope": scope,
            "role": role,
            "user_id": user_id,
            "exp": expire
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token

    @staticmethod
    def decode_token(token: str) -> UserContext:
        """
        Decodes and verifies a JWT token. Raises ValueError if invalid.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return UserContext(
                scope=payload.get("scope"),
                role=payload.get("role"),
                user_id=payload.get("user_id")
            )
        except jwt.ExpiredSignatureError as e:
            logger.error(f"JWT Token expired: {e}")
            raise ValueError("JWT Token has expired")
        except jwt.PyJWTError as e:
            logger.error(f"JWT Token validation failed: {e}")
            raise ValueError(f"Invalid JWT Token: {e}")
