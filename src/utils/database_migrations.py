"""Module: database_migrations.py

Description:
    Database migration utilities for the statechecker server.

    This module handles automatic creation of required database tables
    and schema migrations. Tables are created if they don't exist.
"""

from __future__ import annotations

import mysql.connector
from typing import Optional

import configUtils as ConfigUtils


def get_db_connection():
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


def table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists in the database.

    Args:
        cursor: Database cursor.
        table_name (str): Name of the table to check.

    Returns:
        bool: True if table exists.
    """
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    return cursor.fetchone() is not None


def run_migrations(logger: Optional[object] = None) -> None:
    """Run all database migrations.

    Creates required tables if they don't exist.

    Args:
        logger: Optional logger instance for logging migration progress.
    """
    connection = get_db_connection()
    cursor = connection.cursor(buffered=True)

    try:
        # Create config_websites table
        if not table_exists(cursor, 'config_websites'):
            _log(logger, "Creating table: config_websites")
            cursor.execute("""
                CREATE TABLE `config_websites` (
                    `ID` bigint NOT NULL AUTO_INCREMENT,
                    `url` varchar(2048) COLLATE utf8mb4_unicode_ci NOT NULL,
                    `enabled` tinyint NOT NULL DEFAULT '1',
                    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`ID`),
                    UNIQUE KEY `url_unique` (`url`(255))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            connection.commit()
            _log(logger, "Created table: config_websites")

        # Create config_google_drive_folders table
        if not table_exists(cursor, 'config_google_drive_folders'):
            _log(logger, "Creating table: config_google_drive_folders")
            cursor.execute("""
                CREATE TABLE `config_google_drive_folders` (
                    `ID` bigint NOT NULL AUTO_INCREMENT,
                    `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
                    `description` text COLLATE utf8mb4_unicode_ci,
                    `folder_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
                    `stateCheckFrequency_inMinutes` int NOT NULL DEFAULT 1440,
                    `enabled` tinyint NOT NULL DEFAULT '1',
                    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`ID`),
                    UNIQUE KEY `name_unique` (`name`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            connection.commit()
            _log(logger, "Created table: config_google_drive_folders")

        # Create config_settings table for key-value config overrides
        if not table_exists(cursor, 'config_settings'):
            _log(logger, "Creating table: config_settings")
            cursor.execute("""
                CREATE TABLE `config_settings` (
                    `ID` bigint NOT NULL AUTO_INCREMENT,
                    `setting_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
                    `setting_value` text COLLATE utf8mb4_unicode_ci,
                    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (`ID`),
                    UNIQUE KEY `setting_key_unique` (`setting_key`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            connection.commit()
            _log(logger, "Created table: config_settings")

        _log(logger, "Database migrations completed successfully")

    except Exception as e:
        _log(logger, f"Migration error: {e}", is_error=True)
        raise
    finally:
        cursor.close()
        connection.close()


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
        print(f"[MIGRATION] {message}")
