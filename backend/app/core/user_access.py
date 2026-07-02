from typing import Any

DEFAULT_USER_ROLE_CODES = {"USER"}
DEFAULT_USER_PERMISSIONS = {
    "module_ai:chat:query",
    "module_ai:chat:detail",
    "module_ai:chat:create",
    "module_ai:chat:update",
    "module_ai:chat:delete",
    "module_ai:chat:ws",
}


def _has_enabled_role_code(user: Any, codes: set[str]) -> bool:
    """Return True when the user has at least one enabled role code in codes."""
    roles = getattr(user, "roles", None) or []
    normalized_codes = {code.upper() for code in codes}
    for role in roles:
        if getattr(role, "status", 1) != 0:
            continue
        code = (getattr(role, "code", "") or "").strip().upper()
        if code in normalized_codes:
            return True
    return False


def get_default_user_permissions(user: Any) -> set[str]:
    if _has_enabled_role_code(user, DEFAULT_USER_ROLE_CODES):
        return set(DEFAULT_USER_PERMISSIONS)
    return set()
