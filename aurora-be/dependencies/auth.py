"""Authentication dependencies for Aurora

Re-exports from Mentor's dependencies since both modules
run in the same Matrix container.

Usage:
    from aurora_be.dependencies import CurrentUser, TenantContext

    @router.get("/users")
    async def list_users(
        current_user: CurrentUser,
        tenant_context: TenantContext,
    ):
        ...
"""

# Re-export from Mentor (same Matrix container)
from src.modules.mentor.dependencies.auth import (
    CurrentUser,
    UserInfo,
    get_current_user,
    get_current_user_optional,
)
from src.modules.mentor.dependencies.tenant import (
    TenantContext,
    TenantContextInfo,
    get_tenant_context,
    get_tenant_from_path,
)

__all__ = [
    # Auth
    "CurrentUser",
    "UserInfo",
    "get_current_user",
    "get_current_user_optional",
    # Tenant
    "TenantContext",
    "TenantContextInfo",
    "get_tenant_context",
    "get_tenant_from_path",
]
