This repository is programmed to automatically generate browser bookmarks and Brave Search Engine "Goggle" for FMHY.

## Goggle

Use https://search.brave.com/goggles?goggles_id=https%3A%2F%2Fraw.githubusercontent.com%2Ffmhy%2Fbookmarks%2Frefs%2Fheads%2Fmain%2Ffmhy.goggle

The goggles are automatically updated weekly through Github Actions with the new changes from FMHY.

## Bookmarks

Bookmarks are generated as HTML files which can be imported into any web browser.
![](https://i.imgur.com/N2Wfngc.png)

The HTML files are automatically updated weekly with the new changes from FMHY.

### Why?

Web browsers have auto-complete and search functions that are based on bookmarked pages, so its helpful to have interesting sites bookmarked, so you can find them quicker and make sure you are on the right URL.

### How does it look once imported?

![](https://i.imgur.com/h1GfL1W.png)

### How to download the importable HTML files?

![](https://i.imgur.com/e4xN3wy.png)

### How to import them into the browser?

![](https://i.imgur.com/6BpWb1q.png)

### How to automatically sync bookmarks to your local browser? (Windows)

If you want to avoid manually deleting, importing, and organizing the `FMHY` folder on your bookmarks bar, you can use the automated sync tool:

1. **Perform Initial Setup:** Right-click [setup.bat](utils/setup.bat) in the `utils/` directory and choose **Run as Administrator**. This script will configure your browser profile settings and automatically schedule the sync task in Windows.
2. **Pull the latest changes** from the repository (e.g. `git pull`).
3. **(Optional) Run manual sync** at any time by double-clicking [update_bookmarks.bat](utils/update_bookmarks.bat) in the `utils/` directory.

The tool will:
- Auto-detect your Brave, Chrome, or Edge profiles (by actual profile name and email).
- Check if the browser is running and help you close it (or skip update safely if running in background).
- Create a timestamped backup of your current bookmarks in both JSON and HTML format.
- Replace or insert the `FMHY` folder directly at the very front of your browser's bookmarks bar in-place.

#### How to Restore from Backups
If you ever want to restore your bookmarks to a previous state, navigate to the `utils/backups/` directory:
- **Perfect Restore (JSON)**: Close your browser, rename the `Bookmarks_Backup_YYYYMMDD_HHMMSS.json` file to `Bookmarks` (remove the `.json` extension and suffix), and copy/overwrite it into your browser's profile directory.
- **Browser Import (HTML)**: Open your browser's Bookmark Manager (`Ctrl + Shift + O`), click the top-right menu, select **Import bookmarks**, and choose the `Bookmarks_Backup_YYYYMMDD_HHMMSS.html` file.
