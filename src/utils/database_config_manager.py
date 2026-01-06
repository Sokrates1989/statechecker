"""Module: database_config_manager.py

Description:
    Database-backed configuration manager for the statechecker server.

    This module provides functions to read and write configuration
    from the database, replacing the legacy STATECHECKER_SERVER_CONFIG
    and file-based config.txt approach.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import mysql.connector

import configUtils as ConfigUtils


def _get_db_connection():
    """Create a new database connection.

    Returns:
        mysql.connector.connection: Database connection object.
    """
    config_utils = ConfigUtils.ConfigUtils()
    return mysql.connector.connect(
        host=config_utils.getDatabaseHost(),
        user=config_utils.getDatabaseUser(),
        password=config_utils.getDatabasePassword(),
        database=config_utils.getDatabaseName(),
        port=3306
    )


# =============================================================================
# Website Configuration
# =============================================================================

def get_websites_to_check() -> List[str]:
    """Get all enabled websites to check from the database.

    Returns:
        List[str]: List of website URLs to check.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("SELECT url FROM config_websites WHERE enabled = 1 ORDER BY ID")
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return [row[0] for row in results]
    except Exception:
        return []


def add_website(url: str) -> bool:
    """Add a website to monitor.

    If the database is empty but legacy config has websites,
    migrate them first before adding the new one.

    Args:
        url (str): Website URL to add.

    Returns:
        bool: True if added successfully.
    """
    try:
        # Check if database is empty - if so, migrate legacy websites first
        _migrate_legacy_websites_if_needed()

        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute(
            "INSERT IGNORE INTO config_websites (url) VALUES (%s)",
            (url,)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception:
        return False


def _migrate_legacy_websites_if_needed() -> None:
    """Migrate legacy websites to database if DB is empty but legacy has websites.

    This ensures that when a user adds their first website via the admin UI,
    existing legacy websites are preserved by migrating them to the database.
    """
    try:
        # Check if database already has websites
        existing_db_websites = get_websites_to_check()
        if existing_db_websites:
            return  # Database already has websites, no migration needed

        # Get legacy websites from config file or environment
        config_utils = ConfigUtils.ConfigUtils()
        legacy_websites = _get_legacy_websites_only(config_utils)

        if not legacy_websites:
            return  # No legacy websites to migrate

        # Migrate legacy websites to database
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        for url in legacy_websites:
            cursor.execute(
                "INSERT IGNORE INTO config_websites (url) VALUES (%s)",
                (url,)
            )
        connection.commit()
        cursor.close()
        connection.close()
    except Exception:
        pass  # Silently fail migration - don't break the add operation


def _get_legacy_websites_only(config_utils) -> list:
    """Get websites from legacy config sources only (not database).

    Args:
        config_utils: ConfigUtils instance.

    Returns:
        list: List of website URLs from legacy sources.
    """
    # Try environment variable first
    websites_to_check = os.environ.get("WEBSITES_TO_CHECK")
    if websites_to_check:
        return [item.strip() for item in websites_to_check.strip().strip("\"").split(',') if item.strip()]

    # Try legacy config file/STATECHECKER_SERVER_CONFIG
    config_array = config_utils.getConfigArray()
    if "websites" in config_array:
        if "websitesToCheck" in config_array["websites"]:
            return config_array["websites"]["websitesToCheck"]

    return []


def remove_website(url: str) -> bool:
    """Remove a website from monitoring.

    Args:
        url (str): Website URL to remove.

    Returns:
        bool: True if removed successfully.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("DELETE FROM config_websites WHERE url = %s", (url,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception:
        return False


def website_exists(url: str) -> bool:
    """Check if a website is already configured.

    Args:
        url (str): Website URL to check.

    Returns:
        bool: True if website exists in config.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("SELECT ID FROM config_websites WHERE url = %s", (url,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None
    except Exception:
        return False


# =============================================================================
# Google Drive Folder Configuration
# =============================================================================

def get_google_drive_folders() -> List[Dict[str, Any]]:
    """Get all enabled Google Drive folders to check from the database.

    Returns:
        List[Dict]: List of folder configurations.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("""
            SELECT name, description, folder_id, stateCheckFrequency_inMinutes 
            FROM config_google_drive_folders 
            WHERE enabled = 1 
            ORDER BY ID
        """)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return [
            {
                "name": row[0],
                "description": row[1] or "",
                "folderID": row[2],
                "stateCheckFrequency_inMinutes": row[3]
            }
            for row in results
        ]
    except Exception:
        return []


def add_google_drive_folder(
    name: str,
    folder_id: str,
    description: str = "",
    frequency_minutes: int = 1440
) -> bool:
    """Add a Google Drive folder to monitor.

    Args:
        name (str): Display name for the folder.
        folder_id (str): Google Drive folder ID.
        description (str): Optional description.
        frequency_minutes (int): Check frequency in minutes.

    Returns:
        bool: True if added successfully.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("""
            INSERT INTO config_google_drive_folders 
            (name, description, folder_id, stateCheckFrequency_inMinutes) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                description = VALUES(description),
                folder_id = VALUES(folder_id),
                stateCheckFrequency_inMinutes = VALUES(stateCheckFrequency_inMinutes),
                enabled = 1
        """, (name, description, folder_id, frequency_minutes))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception:
        return False


def remove_google_drive_folder(name: str) -> bool:
    """Remove a Google Drive folder from monitoring.

    Args:
        name (str): Folder name to remove.

    Returns:
        bool: True if removed successfully.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("DELETE FROM config_google_drive_folders WHERE name = %s", (name,))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception:
        return False


def google_drive_folder_exists(name: str) -> bool:
    """Check if a Google Drive folder is already configured.

    Args:
        name (str): Folder name to check.

    Returns:
        bool: True if folder exists in config.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("SELECT ID FROM config_google_drive_folders WHERE name = %s", (name,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result is not None
    except Exception:
        return False


# =============================================================================
# Settings (Key-Value Config)
# =============================================================================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a setting value from the database.

    Args:
        key (str): Setting key.
        default (Optional[str]): Default value if not found.

    Returns:
        Optional[str]: Setting value or default.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("SELECT setting_value FROM config_settings WHERE setting_key = %s", (key,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result[0] if result else default
    except Exception:
        return default


def set_setting(key: str, value: str) -> bool:
    """Set a setting value in the database.

    Args:
        key (str): Setting key.
        value (str): Setting value.

    Returns:
        bool: True if set successfully.
    """
    try:
        connection = _get_db_connection()
        cursor = connection.cursor(buffered=True)
        cursor.execute("""
            INSERT INTO config_settings (setting_key, setting_value) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """, (key, value))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception:
        return False


def get_setting_json(key: str, default: Any = None) -> Any:
    """Get a JSON setting value from the database.

    Args:
        key (str): Setting key.
        default (Any): Default value if not found or parse error.

    Returns:
        Any: Parsed JSON value or default.
    """
    raw = get_setting(key)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def set_setting_json(key: str, value: Any) -> bool:
    """Set a JSON setting value in the database.

    Args:
        key (str): Setting key.
        value (Any): Value to JSON-encode and store.

    Returns:
        bool: True if set successfully.
    """
    return set_setting(key, json.dumps(value))


# =============================================================================
# Frequency Overrides
# =============================================================================

def get_tool_frequency_overrides() -> Dict[str, int]:
    """Get tool frequency overrides from database.

    Returns:
        Dict[str, int]: Mapping of tool name to frequency in minutes.
    """
    return get_setting_json("toolsUsingApi_frequencyOverrides", {})


def set_tool_frequency_override(tool_name: str, frequency_minutes: int) -> bool:
    """Set a tool frequency override.

    Args:
        tool_name (str): Tool name.
        frequency_minutes (int): Frequency in minutes.

    Returns:
        bool: True if set successfully.
    """
    overrides = get_tool_frequency_overrides()
    overrides[tool_name] = frequency_minutes
    return set_setting_json("toolsUsingApi_frequencyOverrides", overrides)


def get_backup_frequency_overrides() -> Dict[str, int]:
    """Get backup frequency overrides from database.

    Returns:
        Dict[str, int]: Mapping of backup name to frequency in minutes.
    """
    return get_setting_json("backupFrequencyOverrides", {})


def set_backup_frequency_override(backup_name: str, frequency_minutes: int) -> bool:
    """Set a backup frequency override.

    Args:
        backup_name (str): Backup name.
        frequency_minutes (int): Frequency in minutes.

    Returns:
        bool: True if set successfully.
    """
    overrides = get_backup_frequency_overrides()
    overrides[backup_name] = frequency_minutes
    return set_setting_json("backupFrequencyOverrides", overrides)


# =============================================================================
# Initial Seeding from Environment Variables
# =============================================================================

def seed_from_env(logger: Optional[object] = None) -> None:
    """Seed the database with initial config from environment variables.

    This function checks for INIT_WEBSITES and INIT_GOOGLE_DRIVE_FOLDERS
    environment variables and seeds the database if the tables are empty.

    Args:
        logger: Optional logger instance.
    """
    _seed_websites_from_env(logger)
    _seed_google_drive_from_env(logger)


def _seed_websites_from_env(logger: Optional[object] = None) -> None:
    """Seed websites from INIT_WEBSITES environment variable.

    Format: comma-separated list of URLs.
    Example: INIT_WEBSITES=https://example.com,https://another.com

    Args:
        logger: Optional logger instance.
    """
    init_websites = os.environ.get("INIT_WEBSITES", "").strip()
    if not init_websites:
        return

    # Check if we already have websites configured
    existing = get_websites_to_check()
    if existing:
        _log(logger, "Websites already configured, skipping seed")
        return

    websites = [w.strip() for w in init_websites.split(",") if w.strip()]
    for url in websites:
        if add_website(url):
            _log(logger, f"Seeded website: {url}")


def _seed_google_drive_from_env(logger: Optional[object] = None) -> None:
    """Seed Google Drive folders from INIT_GOOGLE_DRIVE_FOLDERS environment variable.

    Format: JSON array of folder objects.
    Example: INIT_GOOGLE_DRIVE_FOLDERS=[{"name":"Backup","folderID":"abc123","stateCheckFrequency_inMinutes":1440}]

    Args:
        logger: Optional logger instance.
    """
    init_folders = os.environ.get("INIT_GOOGLE_DRIVE_FOLDERS", "").strip()
    if not init_folders:
        return

    # Check if we already have folders configured
    existing = get_google_drive_folders()
    if existing:
        _log(logger, "Google Drive folders already configured, skipping seed")
        return

    try:
        folders = json.loads(init_folders)
        if not isinstance(folders, list):
            return

        for folder in folders:
            if not isinstance(folder, dict):
                continue
            name = folder.get("name", "")
            folder_id = folder.get("folderID", "")
            if not name or not folder_id:
                continue

            if add_google_drive_folder(
                name=name,
                folder_id=folder_id,
                description=folder.get("description", ""),
                frequency_minutes=int(folder.get("stateCheckFrequency_inMinutes", 1440))
            ):
                _log(logger, f"Seeded Google Drive folder: {name}")

    except json.JSONDecodeError:
        _log(logger, "Failed to parse INIT_GOOGLE_DRIVE_FOLDERS as JSON", is_error=True)


def _log(logger: Optional[object], message: str, is_error: bool = False) -> None:
    """Log a message using logger if available, otherwise print.

    Args:
        logger: Optional logger instance.
        message (str): Message to log.
        is_error (bool): Whether this is an error message.
    """
    if logger:
        if is_error:
            logger.logError(message)
        else:
            logger.logInformation(message)
    else:
        print(f"[CONFIG] {message}")
