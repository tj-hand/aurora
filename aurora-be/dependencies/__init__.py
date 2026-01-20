"""Aurora dependencies package

Re-exports dependencies from Mentor for convenience.
Both Aurora and Mentor run in the same Matrix container.
"""

from .auth import CurrentUser, TenantContext, get_current_user, get_tenant_context

__all__ = [
    "CurrentUser",
    "TenantContext",
    "get_current_user",
    "get_tenant_context",
]
