"""Authentication placeholder.

Currently a no-op. To enable API key authentication:

1. Add API keys to your environment:
       API_KEYS=key1,key2,key3

2. Replace the body of `verify_api_key` with:
       if not x_api_key or x_api_key not in _load_api_keys():
           raise HTTPException(status_code=401, detail="Invalid or missing API key")

3. Optionally add the dependency to any router:
       router = APIRouter(dependencies=[Depends(verify_api_key)])

To enable JWT bearer authentication, replace this module with a proper
JWT decode flow (e.g. python-jose) and adjust the `verify_api_key` signature.
"""

from __future__ import annotations

from fastapi import Header


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """API key gate — currently disabled (pass-through)."""
    # Authentication is disabled. Uncomment below to enable:
    # import os
    # keys = set(os.getenv("API_KEYS", "").split(","))
    # if not x_api_key or x_api_key not in keys:
    #     from fastapi import HTTPException
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    pass
