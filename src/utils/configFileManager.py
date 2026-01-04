"""Module: configFileManager.py

Description:
    Central file-based configuration management for the statechecker server.

    This module resolves the active config file path, loads JSON config,
    and persists config updates atomically.

    Before every write, it creates:
    - A one-time "original" snapshot (config_original.json)
    - A timestamped backup snapshot (config_YYYYmmdd_HHMMSS.json)

    The default persisted config location is:
        <repo_root>/logs/config.txt

    This works well with the existing Docker Compose mount for ../logs -> /code/logs,
    so config changes survive container restarts.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional


_CONFIG_WRITE_LOCK = threading.Lock()


def resolve_config_file_path() -> Path:
    """Resolve the active config file path.

    Resolution order:
        1) `STATECHECKER_CONFIG_FILE` environment variable
        2) `<repo_root>/logs/config.txt` (preferred persistent location)
        3) `<repo_root>/config.txt` (legacy location)

    Returns:
        Path: The resolved config file path.
    """

    repo_root = Path(__file__).resolve().parents[2]

    legacy_config = repo_root / "config.txt"

    explicit = os.getenv("STATECHECKER_CONFIG_FILE")
    if explicit:
        return Path(explicit)

    logs_config = repo_root / "logs" / "config.txt"
    # Prefer an existing persisted config.
    if logs_config.exists():
        return logs_config

    # Respect existing legacy config.txt deployments.
    if legacy_config.exists():
        return legacy_config

    # For new setups: prefer the persisted location when logs/ exists.
    if logs_config.parent.exists():
        return logs_config

    return legacy_config


def is_file_based_config_available() -> bool:
    """Check whether file-based config is available.

    Returns:
        bool: True if the resolved config file exists.
    """

    return resolve_config_file_path().exists()


def load_config(config_file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the config JSON from disk.

    Args:
        config_file_path (Optional[Path]): Explicit config path. If omitted, the
            resolved config file path is used.

    Returns:
        Dict[str, Any]: Parsed JSON config.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """

    path = config_file_path or resolve_config_file_path()
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_backup_dir(config_file_path: Path) -> Path:
    """Ensure the backup directory exists.

    Args:
        config_file_path (Path): The config file path.

    Returns:
        Path: The backup directory path.
    """

    backup_dir = config_file_path.parent / "config_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _create_one_time_original_backup(config_file_path: Path, backup_dir: Path) -> None:
    """Create a one-time "original" backup if it does not exist.

    Args:
        config_file_path (Path): The config file to backup.
        backup_dir (Path): Directory to store backups.
    """

    original_path = backup_dir / "config_original.json"
    if original_path.exists():
        return
    shutil.copy2(config_file_path, original_path)


def ensure_original_backup_exists(config_file_path: Optional[Path] = None) -> Optional[Path]:
    """Ensure the one-time original backup exists.

    This is intended to be called on startup so that even manual edits to
    config.txt later on can be recovered by comparing against the original.

    Args:
        config_file_path (Optional[Path]): Explicit config path. If omitted, the
            resolved config file path is used.

    Returns:
        Optional[Path]: The original backup path if created or already present,
        otherwise `None` if the config file does not exist.
    """

    path = config_file_path or resolve_config_file_path()
    if not path.exists():
        return None

    with _CONFIG_WRITE_LOCK:
        backup_dir = _ensure_backup_dir(path)
        _create_one_time_original_backup(path, backup_dir)
        original_path = backup_dir / "config_original.json"
        return original_path if original_path.exists() else None


def _create_timestamped_backup(config_file_path: Path, backup_dir: Path) -> Path:
    """Create a timestamped backup snapshot of the config.

    Args:
        config_file_path (Path): The config file to backup.
        backup_dir (Path): Directory to store backups.

    Returns:
        Path: The created backup file path.
    """

    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"config_{ts}.json"
    shutil.copy2(config_file_path, backup_path)
    return backup_path


def save_config(config: Dict[str, Any], config_file_path: Optional[Path] = None) -> None:
    """Persist a config dict to disk atomically, with backups.

    Args:
        config (Dict[str, Any]): Config JSON to persist.
        config_file_path (Optional[Path]): Explicit config path. If omitted, the
            resolved config file path is used.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """

    path = config_file_path or resolve_config_file_path()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with _CONFIG_WRITE_LOCK:
        backup_dir = _ensure_backup_dir(path)
        _create_one_time_original_backup(path, backup_dir)
        _create_timestamped_backup(path, backup_dir)

        serialized = json.dumps(config, indent=4)
        tmp_dir = str(path.parent)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=tmp_dir, encoding="utf-8") as tmp:
            tmp.write(serialized)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)

        os.replace(tmp_path, path)


def update_config(update_fn: Callable[[Dict[str, Any]], Dict[str, Any]], config_file_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load, update and persist config in one operation.

    Args:
        update_fn (Callable[[Dict[str, Any]], Dict[str, Any]]): Update function.
            Receives the current config dict and must return the updated config dict.
        config_file_path (Optional[Path]): Explicit config path. If omitted, the
            resolved config file path is used.

    Returns:
        Dict[str, Any]: The updated config that was written.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If update_fn returns a non-dict.
    """

    path = config_file_path or resolve_config_file_path()
    current = load_config(path)
    updated = update_fn(current)
    if not isinstance(updated, dict):
        raise ValueError("update_fn must return a dict")
    save_config(updated, path)
    return updated
