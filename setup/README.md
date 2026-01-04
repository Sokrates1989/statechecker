# 🔧 Setup Directory

This directory contains setup helpers and configuration templates.

<br>

## Table of Contents

1. [📖 Overview](#overview)
2. [🧑‍💻 Usage](#usage)
3. [🧠 Notes](#notes)
4. [🚀 Summary](#summary)

<br>

# 📖 Overview

The `setup/` directory contains templates and helper scripts used by the project quick-start.

## 📁 Structure

```
setup/
├── .env.template          # Environment configuration template
├── modules/               # Helper scripts
│   ├── db_helpers.sh      # DB init selection (schema vs backup) + safe reinstall
│   ├── db_helpers.ps1     # DB init selection (schema vs backup) + safe reinstall
│   ├── docker_helpers.sh  # Bash Docker utilities
│   ├── docker_helpers.ps1 # PowerShell Docker utilities
│   ├── menu_handlers.sh   # Bash menu handlers
│   └── menu_handlers.ps1  # PowerShell menu handlers
└── README.md
```

## 🚀 Quick Start

# 🧑‍💻 Usage

1. Copy `.env.template` to `.env` in the project root:
   ```bash
   cp setup/.env.template .env
   ```

2. Edit `.env` with your configuration

3. Run quick-start:
   ```bash
   ./quick-start.sh      # Linux/Mac
   .\quick-start.ps1     # Windows
   ```

## 📝 Configuration Options

# 🧠 Notes

See `.env.template` for all available configuration options including:
- Docker image settings
- Database configuration
- API settings
- Telegram/Email notification settings
- Check frequency settings

Database initialization notes:

- The default schema file is `install/database/state_checker.sql` (schema-only, no data)
- To restore from backup, place `backup_*.sql` files into `install/database/` and use the quick-start prompt

<br>

# 🚀 Summary

✅ Use `setup/.env.template` to create your repo root `.env`.

✅ Run `quick-start.ps1` / `quick-start.sh` from the repo root.
