# FMHY Bookmarks Sync Utilities

This folder contains automated tools to configure, sync, and manage FMHY browser bookmarks across all Chromium and Firefox browser profiles on Windows.

## Quick Start Guide

1. **Initial Setup Wizard**:
   - Right-click [setup.bat](setup.bat) and select **Run as Administrator**.
   - Select your target browser profile(s) from the interactive list.
   - Enter your desired sync interval in days (e.g. `5`). Windows Task Scheduler will automatically run the sync task anytime your PC is turned on on the scheduled day.

2. **Manual Sync**:
   - Double-click [update_bookmarks.bat](update_bookmarks.bat) at any time to pull and sync the latest FMHY bookmarks on demand.

---

## Utilities Overview

| Script / File | Description |
|---|---|
| [setup.bat](setup.bat) | Administrator setup wizard that runs `create_config.py` and registers the Windows Task Scheduler task. |
| [create_config.py](create_config.py) | Interactive profile scanner and configuration generator (`config.json`). Auto-detects installed browsers, profile emails, source files, and backup retention limits. |
| [update_browser_bookmarks.py](update_browser_bookmarks.py) | Core multi-browser sync engine. Supports Chromium (JSON) and Firefox (SQLite) engines with in-place folder updating at position 0 of the Bookmarks bar. |
| [run_sync.bat](run_sync.bat) | Wrapper script executed by Windows Task Scheduler in non-interactive background mode. |
| [update_bookmarks.bat](update_bookmarks.bat) | Quick shortcut to run manual bookmark sync in interactive mode. |
| [config.json](config.json) | *(Generated)* Local user configuration file storing selected profiles, source files, and backup retention settings. |
| [backups/](backups/) | Structured directory holding timestamped daily backups organized by browser, profile, and date (`YYYY-MM-DD`). |

---

## Supported Browser Families & Forks

The scanner automatically filters for installed browsers on your system:

- **Chromium Family**: Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera (Stable/GX/Crypto), Yandex, Chromium, Thorium, Arc, CentBrowser, Slimjet, Cromite, Ungoogled Chromium (and all Beta/Dev/Canary channels).
- **Firefox / Gecko Family**: Mozilla Firefox, LibreWolf, Waterfox, Floorp, Zen Browser, Pale Moon, SeaMonkey, Tor Browser (and Nightly/Developer channels).

---

## Backups & Retention Policy

Before modifying any bookmarks, the sync engine creates timestamped backups in both native (`.json` or `.sqlite`) and Netscape (`.html`) formats:

```
utils/backups/<Browser>/<Profile>/<YYYY-MM-DD>/
```

### Configurable Retention Limit (`max_backup_days`)
- By default, the tool keeps up to **10 daily backup folders** per profile.
- Older day folders are automatically purged once the count exceeds the limit.
- You can change this limit during setup in `create_config.py` or by editing `"max_backup_days": 10` in `config.json`.

---

## How to Restore Bookmarks

For detailed restoration instructions (Chromium JSON replacement, Firefox SQLite replacement, or HTML import), see the [Backups Guide](backups/README.md).
