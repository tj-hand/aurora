"""
Aurora Backend Module

User management and pre-registration module.
Orchestrates Guardian (identity) + Mentor (tenant association).
"""

__version__ = "0.1.0"
__all__ = [
    "router",
    "register_aurora_actions",
    "get_aurora_action_codes",
    "AURORA_ACTIONS",
]

from .router import router
from .actions import register_aurora_actions, get_aurora_action_codes, AURORA_ACTIONS
