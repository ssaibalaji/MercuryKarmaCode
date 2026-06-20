"""Shared SlowAPI rate-limiter instance.

Defined here (not in main.py) to avoid circular imports: routers import the
limiter and main.py imports the routers, so the limiter must live in a
third module that neither main.py nor any router transitively depends on.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
