#!/usr/bin/env python3

"""Generate config.txt for the statechecker server from environment variables.

This script is intended to run inside the Docker container. It will:

- Create /code/config.txt from config.txt.template + environment variables
  when no config.txt exists yet AND STATECHECKER_SERVER_CONFIG is not set.
- Leave existing config.txt or explicit STATECHECKER_SERVER_CONFIG untouched
  to avoid breaking existing deployments.

Secrets (DB password, email/telegram tokens, etc.) are *not* written into
config.txt. They are expected to be provided via environment variables or
*_FILE secret paths and are resolved at runtime in ConfigUtils.
"""

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_json_template(path: pathlib.Path, fallback: dict) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[WARN] Could not parse JSON template {path}: {exc}", file=sys.stderr)
    return fallback.copy()


def generate_config_if_needed() -> None:
    """Generate /code/config.txt from template + env if appropriate.

    Rules:
    - If config.txt already exists, do nothing (respect existing file).
    - If STATECHECKER_SERVER_CONFIG is set, do nothing (env-driven JSON mode).
    - Otherwise, load config.txt.template and overlay selected values from env.
    """

    config_path = ROOT / "config.txt"

    # 1) Respect existing config.txt
    if config_path.exists():
        print(f"[INFO] Existing config file found at {config_path}, skipping generation.", file=sys.stderr)
        return

    # 2) Respect explicit STATECHECKER_SERVER_CONFIG usage
    if os.environ.get("STATECHECKER_SERVER_CONFIG"):
        print("[INFO] STATECHECKER_SERVER_CONFIG is set; not generating config.txt.", file=sys.stderr)
        return

    # 3) Generate from template + env
    template_path = ROOT / "config.txt.template"
    cfg = _load_json_template(
        template_path,
        {
            "serverAuthenticationToken": "",
            "toolsUsingApi_tolerancePeriod_inSeconds": "100",
            "database": {},
            "telegram": {},
            "email": {},
            "websites": {},
            "googleDrive": {},
        },
    )

    # --- Top-level settings ---
    sat = os.environ.get("SERVER_AUTHENTICATION_TOKEN")
    if sat:
        cfg["serverAuthenticationToken"] = sat

    tol = os.environ.get("TOOLS_USING_API_TOLERANCE_PERIOD_IN_SECONDS")
    if tol:
        cfg["toolsUsingApi_tolerancePeriod_inSeconds"] = str(tol)

    # --- Database section (non-secret fields only) ---
    db = cfg.setdefault("database", {})
    db["host"] = os.environ.get("DB_HOST", db.get("host", "db"))
    db["user"] = os.environ.get("DB_USER", db.get("user", "state_checker"))
    db["database"] = os.environ.get("DB_NAME", db.get("database", "state_checker"))
    db_port = os.environ.get("DB_PORT", db.get("port", "3306"))
    db["port"] = str(db_port)
    # NOTE: password is intentionally *not* filled from env here; ConfigUtils
    # reads DB_PW_FILE / DB_PW first and only falls back to this field.

    # --- Telegram section (non-secret fields only) ---
    tg = cfg.setdefault("telegram", {})
    enabled = os.environ.get("TELEGRAM_ENABLED")
    if enabled:
        tg["enabled"] = str(enabled)

    status_every = os.environ.get("TELEGRAM_STATUS_MESSAGES_EVERY_X_MINUTES")
    if status_every:
        tg["adminStatusMessage_everyXMinutes"] = str(status_every)

    # Bot token and chat IDs remain env/secret-driven; ConfigUtils resolves
    # TELEGRAM_SENDER_BOT_TOKEN(_FILE) and TELEGRAM_RECIPIENTS_*_CHAT_IDS.

    # --- Email section (non-secret fields only) ---
    email = cfg.setdefault("email", {})
    email_enabled = os.environ.get("EMAIL_ENABLED")
    if email_enabled:
        email["enabled"] = str(email_enabled)

    email_status_every = os.environ.get("EMAIL_STATUS_MESSAGES_EVERY_X_MINUTES")
    if email_status_every:
        email["adminStatusMessage_everyXMinutes"] = str(email_status_every)

    # Sender/recipient secrets are env/secret-driven via ConfigUtils.

    # --- Website / Google Drive frequencies (content itself may still live in template) ---
    websites = cfg.setdefault("websites", {})
    check_websites = os.environ.get("CHECK_WEBSITES_EVERY_X_MINUTES")
    if check_websites:
        websites["checkWebSitesEveryXMinutes"] = int(check_websites)

    gdrive = cfg.setdefault("googleDrive", {})
    check_gdrive = os.environ.get("CHECK_GOOGLEDRIVE_EVERY_X_MINUTES")
    if check_gdrive:
        gdrive["checkFilesEveryXMinutes"] = int(check_gdrive)

    # Finally, write out the generated config
    config_path.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
    print(f"[INFO] Generated statechecker config at {config_path}")


def main() -> None:
    generate_config_if_needed()


if __name__ == "__main__":
    main()
