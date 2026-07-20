# FMHY Bookmarks Backups

This folder contains automatic, structured backups of your browser bookmarks created before syncing. 

Backups are organized by **Browser Name**, **Profile Directory**, and **Date**:
```
utils/backups/<Browser>/<Profile_Dir>/<YYYY-MM-DD>/
```
For example:
- `utils/backups/Chrome/Default/2026-07-20/Bookmarks_Backup_105543.json`
- `utils/backups/Firefox/or13i7ii_default_release/2026-07-20/places_Backup_105543.sqlite`

### Automatic Retention Policy
By default, the sync tool automatically keeps up to **10 daily backup folders** per browser profile and automatically purges older day folders. You can change this limit (`max_backup_days`) in `config.json` or during setup in `create_config.py`.

---

## How to Restore

### Option 1: Direct File Replacement (Perfect Restore - Chromium)
1. Close your browser completely.
2. Open the date folder (e.g. `2026-07-20`) containing the JSON backup file you want to restore (`Bookmarks_Backup_HHMMSS.json`).
3. Copy the file, rename it to `Bookmarks` (remove `_Backup_HHMMSS` and `.json`), and overwrite your profile's `Bookmarks` file (e.g. `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Bookmarks`).
4. Reopen your browser.

### Option 2: SQLite Database Restore (Firefox)
1. Close Firefox completely.
2. Open the date folder (e.g. `2026-07-20`) containing the SQLite backup file (`places_Backup_HHMMSS.sqlite`).
3. Copy the file, rename it to `places.sqlite`, and overwrite your Firefox profile's `places.sqlite` file (e.g. `%APPDATA%\Mozilla\Firefox\Profiles\<profile>\places.sqlite`).
4. Reopen Firefox.

### Option 3: Browser UI Import (Standard Import)
1. Open your browser's Bookmark Manager (`Ctrl + Shift + O` or `Ctrl + Shift + B`).
2. Select **Import bookmarks** from the menu.
3. Choose the `.html` backup file (`Bookmarks_Backup_HHMMSS.html`).
