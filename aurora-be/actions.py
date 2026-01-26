"""
AURORA Action Registration

Registers AURORA's permission actions with the MENTOR Action Registry.
This module is called at application startup to register all AURORA actions.

AURORA manages user invitations and onboarding. These actions allow permission
control over invitation management capabilities.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# AURORA action definitions
# Each action follows the format: module.resource.operation
# Translation keys follow ECHOES convention: {module}.actions.{resource}.{operation}.name/description

AURORA_ACTIONS: List[Dict[str, Any]] = [
    # Invitation viewing - who can see invitations
    {
        "resource": "invitations",
        "operation": "view",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
    # Invitation creation - who can send invitations
    {
        "resource": "invitations",
        "operation": "create",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
    # Invitation revocation - who can revoke pending invitations
    {
        "resource": "invitations",
        "operation": "revoke",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
    # User management - who can view users in a tenant
    {
        "resource": "users",
        "operation": "view",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
    # User creation - who can create users directly (without invitation)
    {
        "resource": "users",
        "operation": "create",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
    # User update - who can modify user settings
    {
        "resource": "users",
        "operation": "update",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
    # User deactivation - who can deactivate users
    {
        "resource": "users",
        "operation": "deactivate",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": False,
    },
]


def register_aurora_actions():
    """
    Register all AURORA actions with the MENTOR Action Registry.

    This function should be called at application startup. It safely imports
    from MENTOR to avoid circular dependencies.

    Returns:
        List of registered actions, or empty list if registration failed
    """
    try:
        # Import from MENTOR to access the action registry
        # This import is done here to avoid circular dependencies
        from src.modules.mentor import (
            get_action_registry,
            ActionScope,
        )

        registry = get_action_registry()

        # Convert scope strings to ActionScope enums
        actions_with_scopes = []
        for action in AURORA_ACTIONS:
            action_copy = action.copy()
            action_copy["valid_scopes"] = [
                ActionScope(s) for s in action["valid_scopes"]
            ]
            actions_with_scopes.append(action_copy)

        registered = registry.register_module_actions(
            module="aurora",
            actions=actions_with_scopes,
            default_category="aurora",
        )

        logger.info(f"Registered {len(registered)} AURORA actions with MENTOR")
        return registered

    except ImportError as e:
        logger.warning(
            f"Could not import MENTOR action registry: {e}. "
            "AURORA actions will not be registered."
        )
        return []
    except Exception as e:
        logger.error(f"Failed to register AURORA actions: {e}")
        return []


def get_aurora_action_codes() -> List[str]:
    """
    Get list of all AURORA action codes.

    Useful for validation or testing.

    Returns:
        List of action codes (e.g., ['aurora.invitations.view', 'aurora.invitations.create'])
    """
    return [
        f"aurora.{action['resource']}.{action['operation']}"
        for action in AURORA_ACTIONS
    ]


# Auto-register on import if MENTOR is available
# This allows registration when the module is loaded at startup
try:
    register_aurora_actions()
except Exception:
    # Silently fail - will be retried at explicit startup call
    pass
