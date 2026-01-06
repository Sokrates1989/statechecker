"""Module: startup.py

Description:
    Startup initialization for the statechecker server.

    This module handles database migrations and initial seeding
    when the API or check service starts.
"""

from __future__ import annotations

import os
from typing import Optional


def initialize(logger: Optional[object] = None) -> None:
    """Run all startup initialization tasks.

    This function should be called once when the application starts.
    It runs database migrations and seeds initial data from environment variables.

    Args:
        logger: Optional logger instance for logging progress.
    """
    _log(logger, "Starting initialization...")

    # Run database migrations
    try:
        import database_migrations
        database_migrations.run_migrations(logger)
    except Exception as e:
        _log(logger, f"Migration error (may be expected on first run before DB is ready): {e}", is_error=True)

    # Seed initial data from environment variables
    try:
        import database_config_manager as DbConfig
        DbConfig.seed_from_env(logger)
    except Exception as e:
        _log(logger, f"Seeding error: {e}", is_error=True)

    _log(logger, "Initialization complete")


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
        print(f"[STARTUP] {message}", flush=True)
