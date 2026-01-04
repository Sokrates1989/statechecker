"""Module: telegramAdminActions.py

Description:
    Admin action helpers for the Telegram admin bot listener.

    This module contains:
    - Authorization via configured Telegram chat IDs
    - Parsing target names from HTML-formatted alert messages
    - Applying admin actions by updating persisted config and cleaning DB
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import re

import configFileManager as ConfigFileManager
import databaseWrapper as DatabaseWrapper


def get_admin_chat_ids(config_utils) -> List[str]:
    """Get all allowed chat IDs for admin actions.

    Args:
        config_utils: ConfigUtils instance.

    Returns:
        List[str]: Allowed chat IDs (as strings).
    """

    ids: List[str] = []
    try:
        ids.extend(config_utils.getTelegramErrorChatsIDs() or [])
    except Exception:
        pass
    try:
        ids.extend(config_utils.getTelegramInfoChatsIDs() or [])
    except Exception:
        pass

    return [str(x).strip() for x in ids if str(x).strip()]


def is_allowed_chat(config_utils, chat_id: Any) -> bool:
    """Check whether a chat id is allowed to perform admin actions.

    Args:
        config_utils: ConfigUtils instance.
        chat_id (Any): Incoming Telegram chat id.

    Returns:
        bool: True if allowed.
    """

    allowed = set(get_admin_chat_ids(config_utils))
    return str(chat_id) in allowed


def extract_target_name_from_message_text(message_text: str) -> Optional[str]:
    """Extract the watched item's name from a statechecker alert message.

    The check worker sends alert messages of the form:
        "Your tool is DOWN!\n\n<name>\n..."

    With HTML enabled, the name line is typically wrapped as <b>NAME</b>.

    Args:
        message_text (str): Telegram message text.

    Returns:
        Optional[str]: Extracted name/URL, or None.
    """

    if not message_text:
        return None

    lines = [line.strip() for line in message_text.splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    return re.sub(r"<[^>]*>", "", lines[1]).strip()


def ensure_list(value: Any) -> List[Any]:
    """Normalize a value into a list.

    Args:
        value (Any): Value to normalize.

    Returns:
        List[Any]: A list (empty if not already a list).
    """

    return value if isinstance(value, list) else []


def dedupe_preserve_order(items: List[Any]) -> List[Any]:
    """Deduplicate a list while preserving order.

    Args:
        items (List[Any]): Input list.

    Returns:
        List[Any]: Deduplicated list.
    """

    seen = set()
    out: List[Any] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def remove_website_from_config(cfg: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Remove a website URL from the persisted config.

    Args:
        cfg (Dict[str, Any]): Current config.
        url (str): Website URL.

    Returns:
        Dict[str, Any]: Updated config.
    """

    websites = cfg.setdefault("websites", {})
    websites["websitesToCheck"] = [item for item in ensure_list(websites.get("websitesToCheck")) if item != url]
    return cfg


def add_website_to_config(cfg: Dict[str, Any], url: str) -> Dict[str, Any]:
    """Add a website URL to the persisted config.

    Args:
        cfg (Dict[str, Any]): Current config.
        url (str): Website URL.

    Returns:
        Dict[str, Any]: Updated config.
    """

    websites = cfg.setdefault("websites", {})
    websites["websitesToCheck"] = dedupe_preserve_order(ensure_list(websites.get("websitesToCheck")) + [url])
    return cfg


def remove_google_drive_folder_from_config(cfg: Dict[str, Any], name: str) -> Tuple[Dict[str, Any], bool]:
    """Remove a Google Drive folder backup config entry by name.

    Args:
        cfg (Dict[str, Any]): Current config.
        name (str): Folder/backup name.

    Returns:
        Tuple[Dict[str, Any], bool]: Updated config and whether a folder was removed.
    """

    google_drive = cfg.setdefault("googleDrive", {})
    folders = ensure_list(google_drive.get("foldersToCheck"))

    removed = any(isinstance(f, dict) and f.get("name") == name for f in folders)
    if removed:
        google_drive["foldersToCheck"] = [
            f for f in folders if not (isinstance(f, dict) and f.get("name") == name)
        ]
    return cfg, removed


def apply_admin_action(action: str, target_type: str, target_name: str) -> str:
    """Apply an admin action.

    Args:
        action (str): Action name.
        target_type (str): Target type ('tool'|'website'|'backup').
        target_name (str): Target name or URL.

    Returns:
        str: Human-readable summary.

    Raises:
        ValueError: If action/target_type is unsupported.
    """

    if action == "unwatch" and target_type == "tool":

        try:
            DatabaseWrapper.DatabaseWrapper().deleteToolCheckByName(target_name)
        except Exception:
            pass

        return (
            "Unwatched successfully.\n\n"
            "The tool will be re-watched automatically when it sends a new ping.\n\n"
            "If DOWN alerts come too early, increase the check frequency in the admin UI."
        )

    if action == "unwatch" and target_type == "website":

        if not ConfigFileManager.is_file_based_config_available():
            raise ValueError("file-based config is not available")

        def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
            return remove_website_from_config(cfg, target_name)

        ConfigFileManager.update_config(_update)

        try:
            DatabaseWrapper.DatabaseWrapper().deleteWebsiteCheckByName(target_name)
        except Exception:
            pass

        return "Website removed from watchlist.\n\nUse the button below to re-watch if needed."

    if action == "watch" and target_type == "website":

        if not ConfigFileManager.is_file_based_config_available():
            raise ValueError("file-based config is not available")

        def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
            return add_website_to_config(cfg, target_name)

        ConfigFileManager.update_config(_update)

        return f"Website '{target_name}' added back to config"

    if action == "unwatch" and target_type == "backup":

        removed_from_gdrive = False
        if ConfigFileManager.is_file_based_config_available():

            summary: Dict[str, bool] = {"removed": False}

            def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
                updated, removed = remove_google_drive_folder_from_config(cfg, target_name)
                summary["removed"] = removed
                return updated

            ConfigFileManager.update_config(_update)
            removed_from_gdrive = bool(summary.get("removed"))

        try:
            DatabaseWrapper.DatabaseWrapper().deleteBackupCheckByName(target_name)
        except Exception:
            pass

        if removed_from_gdrive:
            return (
                "Backup unwatched.\n\n"
                "Removed from Google Drive folder config.\n\n"
                "Adjust check frequency in the admin UI if needed."
            )

        return (
            "Backup unwatched.\n\n"
            "The backup will be re-watched automatically when a new ping arrives.\n\n"
            "Adjust check frequency in the admin UI if needed."
        )

    if action == "ignore" and target_type == "tool":
        return apply_admin_action("unwatch", "tool", target_name)

    raise ValueError(f"Unsupported action={action}, target_type={target_type}")


def apply_frequency_change(target_type: str, target_name: str, minutes_value: Any) -> str:
    """Apply a frequency change for a tool or backup.

    This persists an override into config.txt so that client pings cannot
    overwrite the admin setting.

    Args:
        target_type (str): "tool" or "backup".
        target_name (str): Tool/backup name.
        minutes_value (Any): Minutes value from callback data.

    Returns:
        str: Human-readable summary.

    Raises:
        ValueError: If target_type or minutes_value is invalid.
    """

    try:
        minutes_int = int(minutes_value)
    except Exception:
        raise ValueError("invalid frequency")

    if minutes_int <= 0:
        raise ValueError("invalid frequency")

    if not ConfigFileManager.is_file_based_config_available():
        raise ValueError("file-based config is not available")

    if target_type == "tool":

        def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
            overrides = cfg.get("toolsUsingApi_frequencyOverrides")
            if not isinstance(overrides, dict):
                overrides = {}
            overrides[target_name] = minutes_int
            cfg["toolsUsingApi_frequencyOverrides"] = overrides
            return cfg

        ConfigFileManager.update_config(_update)

        try:
            DatabaseWrapper.DatabaseWrapper().updateToolCheckFrequencyByName(target_name, minutes_int)
        except Exception:
            pass

        return f"Tool '{target_name}' frequency set to {minutes_int}m"

    if target_type == "backup":

        def _update(cfg: Dict[str, Any]) -> Dict[str, Any]:
            overrides = cfg.get("backupFrequencyOverrides")
            if not isinstance(overrides, dict):
                overrides = {}
            overrides[target_name] = minutes_int
            cfg["backupFrequencyOverrides"] = overrides
            return cfg

        ConfigFileManager.update_config(_update)

        try:
            DatabaseWrapper.DatabaseWrapper().updateBackupCheckFrequencyByName(target_name, minutes_int)
        except Exception:
            pass

        return f"Backup '{target_name}' frequency set to {minutes_int}m"

    raise ValueError(f"Unsupported target_type={target_type}")
