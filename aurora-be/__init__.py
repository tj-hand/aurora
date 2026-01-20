"""
Aurora Backend Module

User management and pre-registration module.
Orchestrates Guardian (identity) + Mentor (tenant association).
"""

__version__ = "0.1.0"
__all__ = ["router"]

from .router import router
