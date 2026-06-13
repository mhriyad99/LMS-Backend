from fastapi import Header
import jwt

from app.config.security import SECRET_KEY, ALGORITHM
from app.config.schemas import TokenData


async def get_optional_user_id(
    authorization: str | None = Header(default=None),
) -> int | None:
    """
    Extracts user_id from Bearer token if present.
    Returns None for guests (no token or invalid token).
    """
    if not authorization:
        return None

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        return int(user_id)
    except jwt.PyJWTError:
        return None