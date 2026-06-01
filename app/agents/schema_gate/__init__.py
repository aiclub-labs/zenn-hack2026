"""Schema Revision Gate (Req 2.7).

State machine per design.md §4.6:
  CheckRevision -> AllSeen | UnseenExists -> BannerShown -> Acknowledged
  -> AllSeen -> InvokeDeltaDetector
"""
from .gate import SchemaRevisionGate

__all__ = ["SchemaRevisionGate"]
