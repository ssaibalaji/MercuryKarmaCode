"""Shared slowapi rate limiter instance.

Lives in its own module (rather than main.py) so routers can import it
without creating a circular import with the FastAPI app module.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
