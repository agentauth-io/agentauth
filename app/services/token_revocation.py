"""
Token revocation service.

Maintains a blacklist of revoked JWT token IDs (JTIs).
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory revocation store: {jti: expires_at_timestamp}
_REVOKED_TOKENS: dict[str, float] = {}
_MAX_REVOKED = 10000


def revoke_token(jti: str, expires_at: datetime) -> None:
    """Add a token to the revocation blacklist."""
    _REVOKED_TOKENS[jti] = expires_at.timestamp()
    _cleanup()
    logger.info(f"Token revoked: {jti}")


def is_revoked(jti: str) -> bool:
    """Check if a token has been revoked."""
    return jti in _REVOKED_TOKENS


def _cleanup() -> None:
    """Remove expired entries to prevent memory growth."""
    now = time.time()
    expired = [jti for jti, exp in _REVOKED_TOKENS.items() if exp < now]
    for jti in expired:
        del _REVOKED_TOKENS[jti]
    # If still over limit, remove oldest
    if len(_REVOKED_TOKENS) > _MAX_REVOKED:
        sorted_jtis = sorted(_REVOKED_TOKENS, key=lambda k: _REVOKED_TOKENS[k])
        for jti in sorted_jtis[: len(_REVOKED_TOKENS) - _MAX_REVOKED]:
            del _REVOKED_TOKENS[jti]
