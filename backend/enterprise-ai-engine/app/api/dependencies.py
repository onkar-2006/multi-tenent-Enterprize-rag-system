from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import TokenManager, UserContext

# Initialize HTTP Bearer authentication parser
security_bearer = HTTPBearer()

def get_current_user_context(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> UserContext:
    """
    HTTP Authorization Bearer parser dependency.
    Validates JWT token and injects the extracted UserContext (scope, role, user_id).
    """
    try:
        token = credentials.credentials
        user_context = TokenManager.decode_token(token)
        return user_context
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
