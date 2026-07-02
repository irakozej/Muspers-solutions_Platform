import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

# In-memory limiter, fine for single-process dev. Swap to a Redis storage URI for
# multi-worker prod deployments.
limiter = Limiter(key_func=get_remote_address)


def user_or_ip_key(request: Request) -> str:
    """Rate-limit key for authenticated endpoints: per-user, not per-IP.

    Keyed on a hash of the Authorization header so each signed-in user gets
    their own bucket (two clients behind the same office NAT don't throttle
    each other). Falls back to the client IP for unauthenticated requests.
    The raw token never appears in limiter storage or error messages.
    """
    auth = request.headers.get("authorization")
    if auth:
        return "u:" + hashlib.sha256(auth.encode("utf-8")).hexdigest()[:32]
    return "ip:" + get_remote_address(request)
