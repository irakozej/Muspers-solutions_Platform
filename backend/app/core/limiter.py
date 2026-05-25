from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory limiter — fine for single-process dev. Swap to a Redis storage URI for
# multi-worker prod deployments.
limiter = Limiter(key_func=get_remote_address)
