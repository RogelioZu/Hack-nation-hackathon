"""Supabase client for the Python host. Uses the service_role key: never ship this to the browser.

`supabase` is imported only when a client is requested, so modules that merely import this one
(e.g. the Omnigent tools, loaded by the spec loader) do not need it installed.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@lru_cache(maxsize=1)
def client():
    from supabase import create_client  # deferred: only Supabase-persisting tools need it

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the repo-root .env (see .env.example)")
    return create_client(url, key)
