"""Experimental GXP 0.1 reference implementation.

The package deliberately implements an application-level event contract rather
than a replacement network transport. See ``specification/`` for the wire
semantics and ``KNOWN_LIMITATIONS.md`` before any deployment use.
"""

from .models import IngestionAck
from .validation import validate_envelope

__all__ = ["IngestionAck", "validate_envelope"]
__version__ = "0.1.0a1"

