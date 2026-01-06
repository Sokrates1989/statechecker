"""Module: adminApiConfigRoutes.py

Description:
    Admin API endpoints for reading persisted admin-relevant configuration.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, Query

import configFileManager as ConfigFileManager
from adminApiCommon import require_admin_auth, require_admin_auth_readonly


router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/config")
def admin_get_config(
    server_auth_token: Optional[str] = Query(default=None),
    x_server_authentication_token: Optional[str] = Header(
        default=None,
        alias="X-Server-Authentication-Token",
    ),
) -> Dict[str, Any]:
    """Get the persisted config sections relevant for admin management.

    Args:
        server_auth_token (Optional[str]): Token provided as query parameter.
        x_server_authentication_token (Optional[str]): Token provided as header.

    Returns:
        Dict[str, Any]: Admin-relevant config sections.
    """

    require_admin_auth_readonly(server_auth_token, x_server_authentication_token)

    cfg_path = ConfigFileManager.resolve_config_file_path()
    cfg = ConfigFileManager.load_config(cfg_path)

    return {
        "configFilePath": str(cfg_path),
        "websites": cfg.get("websites", {}),
        "googleDrive": cfg.get("googleDrive", {}),
        "toolsUsingApi_frequencyOverrides": cfg.get("toolsUsingApi_frequencyOverrides", {}),
        "backupFrequencyOverrides": cfg.get("backupFrequencyOverrides", {}),
    }
