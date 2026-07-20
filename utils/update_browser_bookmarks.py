#!/usr/bin/env python3
"""Update local browser bookmarks (Chrome, Edge, Brave, Vivaldi, Opera, Firefox, Zen, LibreWolf, etc.) with FMHY bookmarks."""

import os
import sys
import re
import json
import uuid
import time
import shutil
import sqlite3
import subprocess
import copy
import configparser
import base64
from datetime import datetime
from urllib.parse import urlparse

# Path resolution relative to script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
BACKUPS_DIR = os.path.join(SCRIPT_DIR, "backups")

# Executable mappings for process detection and force-closing
BROWSER_EXECUTABLES = {
    "Brave": ["brave.exe"],
    "Chrome": ["chrome.exe"],
    "Edge": ["msedge.exe"],
    "Vivaldi": ["vivaldi.exe"],
    "Opera": ["opera.exe"],
    "Yandex": ["browser.exe", "yandex.exe"],
    "Chromium": ["chrome.exe", "chromium.exe", "thorium.exe", "slimjet.exe", "arc.exe"],
    "Firefox": ["firefox.exe"],
    "LibreWolf": ["librewolf.exe"],
    "Waterfox": ["waterfox.exe"],
    "Floorp": ["floorp.exe"],
    "Zen Browser": ["zen.exe"],
    "Pale Moon": ["palemoon.exe"],
    "SeaMonkey": ["seamonkey.exe"],
    "Tor Browser": ["firefox.exe", "tor.exe"]
}

def clean_profile_name(raw_name):
    if not raw_name:
        return "Default"
    lower = raw_name.lower()
    if lower in ("default-release", "default-nightly", "default", "default profile") or "default-release" in lower or lower.endswith(".default"):
        return "Default"
    return raw_name

# Define search paths for Chromium and Firefox browser profiles on Windows
def find_browser_profiles():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    app_data = os.environ.get("APPDATA", "")
    profiles = []
    
    # 1. Chromium Family Browsers
    chromium_browsers = {
        "Brave": [
            os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data"),
            os.path.join(local_app_data, "BraveSoftware", "Brave-Browser-Beta", "User Data"),
            os.path.join(local_app_data, "BraveSoftware", "Brave-Browser-Nightly", "User Data")
        ],
        "Chrome": [
            os.path.join(local_app_data, "Google", "Chrome", "User Data"),
            os.path.join(local_app_data, "Google", "Chrome Beta", "User Data"),
            os.path.join(local_app_data, "Google", "Chrome Dev", "User Data"),
            os.path.join(local_app_data, "Google", "Chrome SxS", "User Data")
        ],
        "Edge": [
            os.path.join(local_app_data, "Microsoft", "Edge", "User Data"),
            os.path.join(local_app_data, "Microsoft", "Edge Beta", "User Data"),
            os.path.join(local_app_data, "Microsoft", "Edge Dev", "User Data"),
            os.path.join(local_app_data, "Microsoft", "Edge SxS", "User Data")
        ],
        "Vivaldi": [
            os.path.join(local_app_data, "Vivaldi", "User Data"),
            os.path.join(local_app_data, "Vivaldi Snapshot", "User Data")
        ],
        "Opera": [
            os.path.join(app_data, "Opera Software", "Opera Stable"),
            os.path.join(app_data, "Opera Software", "Opera GX Stable"),
            os.path.join(app_data, "Opera Software", "Opera Crypto Stable")
        ],
        "Yandex": [
            os.path.join(local_app_data, "Yandex", "YandexBrowser", "User Data")
        ],
        "Chromium": [
            os.path.join(local_app_data, "Chromium", "User Data"),
            os.path.join(local_app_data, "Thorium", "User Data"),
            os.path.join(local_app_data, "Arc", "User Data"),
            os.path.join(local_app_data, "CentBrowser", "User Data"),
            os.path.join(local_app_data, "Slimjet", "User Data"),
            os.path.join(local_app_data, "Cromite", "User Data"),
            os.path.join(local_app_data, "Ungoogled Chromium", "User Data")
        ]
    }
    
    for browser_name, paths in chromium_browsers.items():
        if not find_browser_executable(browser_name):
            continue
        for user_data_path in paths:
            if not os.path.exists(user_data_path):
                continue
            direct_bookmarks = os.path.join(user_data_path, "Bookmarks")
            if os.path.isfile(direct_bookmarks):
                profiles.append({
                    "browser": browser_name,
                    "type": "chromium",
                    "profile_dir": "Default",
                    "profile_name": browser_name,
                    "email": None,
                    "path": direct_bookmarks,
                    "dir": user_data_path
                })
            else:
                try:
                    for item in os.listdir(user_data_path):
                        profile_path = os.path.join(user_data_path, item)
                        if os.path.isdir(profile_path):
                            bookmarks_file = os.path.join(profile_path, "Bookmarks")
                            preferences_file = os.path.join(profile_path, "Preferences")
                            if os.path.isfile(bookmarks_file):
                                friendly_name = None
                                email = None
                                if os.path.isfile(preferences_file):
                                    try:
                                        with open(preferences_file, 'r', encoding='utf-8') as f:
                                            pref_data = json.load(f)
                                        friendly_name = pref_data.get('profile', {}).get('name')
                                        accounts = pref_data.get('account_info', [])
                                        if accounts and isinstance(accounts, list):
                                            email = accounts[0].get('email')
                                        if not email:
                                            email = pref_data.get('google', {}).get('services', {}).get('username')
                                        if not email:
                                            email = pref_data.get('signin', {}).get('connection', {}).get('username')
                                    except Exception:
                                        pass
                                profiles.append({
                                    "browser": browser_name,
                                    "type": "chromium",
                                    "profile_dir": item,
                                    "profile_name": clean_profile_name(friendly_name or item),
                                    "email": email,
                                    "path": bookmarks_file,
                                    "dir": profile_path
                                })
                except Exception:
                    pass

    # 2. Firefox Family Browsers
    firefox_browsers = {
        "Firefox": os.path.join(app_data, "Mozilla", "Firefox"),
        "LibreWolf": os.path.join(app_data, "LibreWolf"),
        "Waterfox": os.path.join(app_data, "Waterfox"),
        "Floorp": os.path.join(app_data, "Floorp"),
        "Zen Browser": os.path.join(app_data, "zen"),
        "Pale Moon": os.path.join(app_data, "Moonchild Productions", "Pale Moon"),
        "SeaMonkey": os.path.join(app_data, "Mozilla", "SeaMonkey"),
        "Tor Browser": os.path.join(app_data, "TorBrowser-Data", "Browser")
    }

    for browser_name, base_path in firefox_browsers.items():
        if not os.path.exists(base_path):
            continue
        if not find_browser_executable(browser_name):
            continue
        profile_names = {}
        ini_path = os.path.join(base_path, "profiles.ini")
        if os.path.isfile(ini_path):
            try:
                cp = configparser.ConfigParser()
                cp.read(ini_path, encoding='utf-8')
                for section in cp.sections():
                    if section.startswith("Profile"):
                        name = cp.get(section, "Name", fallback=None)
                        path_val = cp.get(section, "Path", fallback=None)
                        if path_val:
                            norm_path = os.path.normpath(path_val)
                            folder_name = os.path.basename(norm_path)
                            profile_names[folder_name] = name or folder_name
            except Exception:
                pass

        candidate_dirs = []
        profiles_dir = os.path.join(base_path, "Profiles")
        if os.path.isdir(profiles_dir):
            for d in os.listdir(profiles_dir):
                candidate_dirs.append(os.path.join(profiles_dir, d))
        for d in os.listdir(base_path):
            full = os.path.join(base_path, d)
            if os.path.isdir(full) and full not in candidate_dirs:
                candidate_dirs.append(full)

        for p_dir in candidate_dirs:
            if "backgroundupdate" in p_dir.lower():
                continue
            places_db = os.path.join(p_dir, "places.sqlite")
            if os.path.isfile(places_db):
                folder_name = os.path.basename(p_dir)
                raw_name = profile_names.get(folder_name, folder_name)
                friendly_name = clean_profile_name(raw_name)
                email = None
                signed_in_file = os.path.join(p_dir, "signedInUser.json")
                if os.path.isfile(signed_in_file):
                    try:
                        with open(signed_in_file, 'r', encoding='utf-8') as f:
                            s_data = json.load(f)
                        email = s_data.get("accountData", {}).get("email")
                    except Exception:
                        pass
                profiles.append({
                    "browser": browser_name,
                    "type": "firefox",
                    "profile_dir": folder_name,
                    "profile_name": friendly_name,
                    "email": email,
                    "path": places_db,
                    "dir": p_dir
                })

    return profiles

def find_browser_executable(browser_name):
    """Locate the executable path for the specified browser on Windows."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    
    search_paths = []
    if browser_name == "Brave":
        search_paths = [
            os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(program_files_x86, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "Application", "brave.exe")
        ]
    elif browser_name == "Chrome":
        search_paths = [
            os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe")
        ]
    elif browser_name == "Edge":
        search_paths = [
            os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe")
        ]
    elif browser_name == "Firefox":
        search_paths = [
            os.path.join(program_files, "Mozilla Firefox", "firefox.exe"),
            os.path.join(program_files_x86, "Mozilla Firefox", "firefox.exe")
        ]
    elif browser_name == "Zen Browser":
        search_paths = [
            os.path.join(program_files, "Zen Browser", "zen.exe"),
            os.path.join(local_app_data, "zen", "zen.exe")
        ]
    elif browser_name == "LibreWolf":
        search_paths = [
            os.path.join(program_files, "LibreWolf", "librewolf.exe"),
            os.path.join(local_app_data, "LibreWolf", "librewolf.exe")
        ]
    elif browser_name == "Waterfox":
        search_paths = [
            os.path.join(program_files, "Waterfox", "waterfox.exe"),
            os.path.join(local_app_data, "Waterfox", "waterfox.exe")
        ]
    elif browser_name == "Floorp":
        search_paths = [
            os.path.join(program_files, "Floorp", "floorp.exe"),
            os.path.join(local_app_data, "Floorp", "floorp.exe")
        ]
    elif browser_name == "Vivaldi":
        search_paths = [
            os.path.join(program_files, "Vivaldi", "Application", "vivaldi.exe"),
            os.path.join(local_app_data, "Vivaldi", "Application", "vivaldi.exe")
        ]
    elif browser_name == "Opera":
        search_paths = [
            os.path.join(local_app_data, "Programs", "Opera", "launcher.exe"),
            os.path.join(local_app_data, "Programs", "Opera GX", "launcher.exe")
        ]
        
    for path in search_paths:
        if os.path.isfile(path):
            return path
    return None

def is_browser_running(browser_name):
    exe_names = BROWSER_EXECUTABLES.get(browser_name, [])
    if not exe_names:
        return False
        
    try:
        output = subprocess.check_output("tasklist", shell=True, text=True, errors="ignore").lower()
        return any(exe.lower() in output for exe in exe_names)
    except Exception:
        return False

def check_and_close_browser(browser_name, non_interactive=False):
    exe_names = BROWSER_EXECUTABLES.get(browser_name, [])
    if not exe_names:
        return True
        
    if is_browser_running(browser_name):
        if non_interactive:
            print(f"[INFO] {browser_name} is currently running. Skipping sync to avoid closing active tabs.")
            return False
            
        while is_browser_running(browser_name):
            print(f"\n[WARNING] {browser_name} is currently running!")
            print("Modifying bookmarks while the browser is running will result in changes being overwritten.")
            choice = input(f"Would you like to force close {browser_name} now? (y/n) or press Enter after closing it manually: ").strip().lower()
            if choice == 'y':
                for exe_name in exe_names:
                    try:
                        subprocess.run(["taskkill", "/f", "/im", exe_name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        pass
                time.sleep(1.5)
            else:
                print("Press Enter to verify if the browser is closed...")
                input()
    return True

def select_profile(profiles):
    if not profiles:
        print("No browser profiles found automatically.")
        path = input("Please enter the absolute path to your browser's 'Bookmarks' or 'places.sqlite' file: ").strip()
        if not path:
            print("No path entered. Exiting.")
            sys.exit(1)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
        b_type = "firefox" if path.endswith(".sqlite") else "chromium"
        return {
            "browser": "Custom",
            "type": b_type,
            "profile_dir": "Custom",
            "profile_name": "Custom",
            "email": None,
            "path": path,
            "dir": os.path.dirname(path)
        }
        
    if len(profiles) == 1:
        print(f"Found profile: {profiles[0]['browser']} - {profiles[0]['profile_name']}")
        return profiles[0]
        
    print("\nFound multiple browser profiles:")
    for idx, p in enumerate(profiles):
        display_name = p['profile_name']
        details = []
        if p['email']:
            details.append(p['email'])
        if p['profile_dir'] != display_name:
            details.append(p['profile_dir'])
        details_str = f" ({', '.join(details)})" if details else ""
        print(f"[{idx + 1}] {p['browser']} - {display_name}{details_str}")
    
    try:
        choice = input(f"Select a profile (1-{len(profiles)}) [default 1]: ").strip()
        if not choice:
            return profiles[0]
        idx = int(choice) - 1
        if 0 <= idx < len(profiles):
            return profiles[idx]
    except Exception:
        pass
    
    print("Invalid choice. Defaulting to first profile.")
    return profiles[0]

def parse_bookmarks_html(file_path):
    """Parse Netscape HTML bookmark file into hierarchical JSON format."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract all H3 headers (folders) and A links
    folder_stack = []
    
    # Root folder structure
    root_folder = {
        "type": "folder",
        "name": "FMHY",
        "children": []
    }
    
    # We will build tree using HTML parsing
    from xml.etree import ElementTree
    try:
        import html5lib
        # Fallback if html5lib not available, parse with regex / html.parser
    except ImportError:
        pass

    # Regex based reliable Netscape HTML parser
    lines = content.splitlines()
    
    current_folder_stack = [root_folder]
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        # Match Folder Title: <H3 ...>Title</H3>
        h3_match = re.search(r'<H3[^>]*>(.*?)</H3>', line_str, re.IGNORECASE)
        if h3_match:
            folder_name = h3_match.group(1).strip()
            new_folder = {
                "type": "folder",
                "name": folder_name,
                "children": []
            }
            current_folder_stack[-1]["children"].append(new_folder)
            current_folder_stack.append(new_folder)
            continue
            
        # Match Bookmark URL: <A HREF="url" ...>Title</A>
        a_match = re.search(r'<A\s+HREF="([^"]+)"[^>]*>(.*?)</A>', line_str, re.IGNORECASE)
        if a_match:
            url = a_match.group(1).strip()
            title = a_match.group(2).strip()
            bookmark_node = {
                "type": "url",
                "name": title or url,
                "url": url
            }
            current_folder_stack[-1]["children"].append(bookmark_node)
            continue
            
        # Match end of folder list </DL>
        if re.search(r'</DL>', line_str, re.IGNORECASE):
            if len(current_folder_stack) > 1:
                current_folder_stack.pop()

    return root_folder

def remove_all_folders_named(parent_node, target_name):
    """Recursively removes all folders named target_name from parent_node's children."""
    removed = []
    if "children" in parent_node and isinstance(parent_node["children"], list):
        new_children = []
        for child in parent_node["children"]:
            if child.get("type") == "folder" and child.get("name") == target_name:
                removed.append(child)
            else:
                new_children.append(child)
                # Recurse into subfolders
                if child.get("type") == "folder":
                    sub_removed = remove_all_folders_named(child, target_name)
                    removed.extend(sub_removed)
        parent_node["children"] = new_children
    return removed

def collect_ids(node, existing_ids):
    """Collects all existing numeric and GUID IDs from a bookmark node."""
    if "id" in node:
        existing_ids.add(str(node["id"]))
    if "children" in node and isinstance(node["children"], list):
        for child in node["children"]:
            collect_ids(child, existing_ids)

def prepare_nodes_for_chromium(nodes, next_id_list, date_added):
    """Recursively assigns valid Chrome IDs, GUIDs, and timestamps to new nodes."""
    for node in nodes:
        node["id"] = str(next_id_list[0])
        next_id_list[0] += 1
        node["guid"] = str(uuid.uuid4())
        node["date_added"] = date_added
        if node.get("type") == "folder":
            node["date_modified"] = date_added
            if "children" not in node or not isinstance(node["children"], list):
                node["children"] = []
            prepare_nodes_for_chromium(node["children"], next_id_list, date_added)

def export_bookmarks_to_html(node, file_handle, indent=0):
    spaces = "    " * indent
    if node.get("type") == "folder":
        name = node.get("name", "Folder")
        file_handle.write(f'{spaces}<DT><H3>{name}</H3>\n')
        file_handle.write(f'{spaces}<DL><p>\n')
        for child in node.get("children", []):
            export_bookmarks_to_html(child, file_handle, indent + 1)
        if indent > 0:
            file_handle.write(f'{spaces}</DL><p>\n')
    elif node.get("type") == "url":
        url = node.get("url", "")
        name = node.get("name", "Bookmark")
        file_handle.write(f'{spaces}<DT><A HREF="{url}">{name}</A>\n')

def save_backup_html(bookmarks_data, output_path):
    """Saves a standard Netscape HTML copy of the user's bookmarks."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n")
            f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
            f.write("<TITLE>Bookmarks Backup</TITLE>\n")
            f.write("<H1>Bookmarks Backup</H1>\n")
            f.write("<DL><p>\n")
            for root_name in ["bookmark_bar", "other", "synced"]:
                if root_name in bookmarks_data.get("roots", {}):
                    root_folder = bookmarks_data["roots"][root_name]
                    for child in root_folder.get("children", []):
                        export_bookmarks_to_html(child, f, indent=1)
            f.write("</DL><p>\n")
        try:
            rel_path = os.path.relpath(output_path, SCRIPT_DIR)
        except ValueError:
            rel_path = os.path.basename(output_path)
        print(f"Exported HTML backup of original bookmarks to: {rel_path}")
    except Exception as e:
        print(f"[WARNING] Failed to export HTML bookmarks backup: {e}")

# Firefox helper functions
def generate_firefox_guid():
    return base64.b64encode(uuid.uuid4().bytes, altchars=b'_-').decode('ascii')[:12]

def rev_host(url):
    try:
        host = urlparse(url).netloc
        if host:
            parts = host.split('.')
            parts.reverse()
            return '.'.join(parts) + '.'
    except Exception:
        pass
    return ''

def remove_firefox_bookmark_tree(cursor, bookmark_id):
    cursor.execute("SELECT id, type, fk FROM moz_bookmarks WHERE parent = ?", (bookmark_id,))
    children = cursor.fetchall()
    for child_id, child_type, fk in children:
        remove_firefox_bookmark_tree(cursor, child_id)
        
    cursor.execute("SELECT fk FROM moz_bookmarks WHERE id = ?", (bookmark_id,))
    row = cursor.fetchone()
    if row and row[0]:
        fk = row[0]
        cursor.execute("UPDATE moz_places SET foreign_count = MAX(0, foreign_count - 1) WHERE id = ?", (fk,))
        
    cursor.execute("DELETE FROM moz_bookmarks WHERE id = ?", (bookmark_id,))

def insert_firefox_bookmark_node(cursor, node, parent_id, position):
    now_usec = int(time.time() * 1000000)
    guid = generate_firefox_guid()
    node_type = node.get("type", "folder")
    title = node.get("name", "Bookmark")
    
    if node_type == "folder":
        cursor.execute(
            "INSERT INTO moz_bookmarks (type, fk, parent, position, title, dateAdded, lastModified, guid) VALUES (2, NULL, ?, ?, ?, ?, ?, ?)",
            (parent_id, position, title, now_usec, now_usec, guid)
        )
        folder_id = cursor.lastrowid
        children = node.get("children", [])
        for idx, child in enumerate(children):
            insert_firefox_bookmark_node(cursor, child, folder_id, idx)
        return folder_id
    elif node_type == "url":
        url = node.get("url", "")
        if not url:
            return None
        cursor.execute("SELECT id FROM moz_places WHERE url = ?", (url,))
        place_row = cursor.fetchone()
        if place_row:
            place_id = place_row[0]
            cursor.execute("UPDATE moz_places SET foreign_count = foreign_count + 1 WHERE id = ?", (place_id,))
        else:
            place_guid = generate_firefox_guid()
            r_host = rev_host(url)
            cursor.execute(
                "INSERT INTO moz_places (url, title, rev_host, hidden, typed, frecency, guid, foreign_count) VALUES (?, ?, ?, 0, 0, 100, ?, 1)",
                (url, title, r_host, place_guid)
            )
            place_id = cursor.lastrowid
            
        cursor.execute(
            "INSERT INTO moz_bookmarks (type, fk, parent, position, title, dateAdded, lastModified, guid) VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
            (place_id, parent_id, position, title, now_usec, now_usec, guid)
        )
        return cursor.lastrowid

def read_firefox_bookmarks_as_dict(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, url FROM moz_places")
    urls = dict(c.fetchall())
    c.execute("SELECT id, type, parent, title, fk FROM moz_bookmarks")
    rows = c.fetchall()

    nodes = {}
    for bm_id, b_type, parent_id, title, fk in rows:
        if b_type == 1:
            nodes[bm_id] = {'type': 'url', 'name': title or '', 'url': urls.get(fk, ''), 'parent_id': parent_id}
        elif b_type == 2:
            nodes[bm_id] = {'type': 'folder', 'name': title or '', 'children': [], 'parent_id': parent_id}

    for bm_id, node in nodes.items():
        p_id = node.get('parent_id')
        if p_id in nodes and p_id != bm_id:
            nodes[p_id]['children'].append(node)

    toolbar_children = nodes.get(3, {}).get('children', [])
    other_children = nodes.get(2, {}).get('children', []) + nodes.get(4, {}).get('children', []) + nodes.get(5, {}).get('children', [])
    conn.close()
    return {
        "roots": {
            "bookmark_bar": {"children": toolbar_children},
            "other": {"children": other_children}
        }
    }

def update_firefox_places_sqlite(db_path, new_root_folder):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id FROM moz_bookmarks WHERE guid = 'toolbar_____' OR (parent = 1 AND title = 'toolbar')")
    row = c.fetchone()
    toolbar_id = row[0] if row else 3

    c.execute("SELECT id FROM moz_bookmarks WHERE parent = ? AND title = 'FMHY'", (toolbar_id,))
    rows = c.fetchall()
    for row in rows:
        remove_firefox_bookmark_tree(c, row[0])

    c.execute("UPDATE moz_bookmarks SET position = position + 1 WHERE parent = ?", (toolbar_id,))
    insert_firefox_bookmark_node(c, new_root_folder, toolbar_id, 0)
    conn.commit()
    conn.close()

def main():
    non_interactive = "--non-interactive" in sys.argv
    
    print("====================================================")
    print("  Browser Bookmarks Automatic Updater (FMHY)")
    print("====================================================\n")
    
    # 1. Load config if exists
    config = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"[INFO] Loaded config containing {len(config.get('profiles', []))} profiles")
        except Exception as e:
            print(f"[WARNING] Could not parse config.json: {e}")
            
    # Rebuild bookmarks if configured or missing
    rebuild_first = config.get("rebuild_first", True) if config else True
    source_file = config.get("source_file", "fmhy_in_bookmarks.html") if config else "fmhy_in_bookmarks.html"
    source_path = os.path.join(ROOT_DIR, source_file)
    
    if rebuild_first or not os.path.exists(source_path):
        make_script = os.path.join(ROOT_DIR, "make_fmhy_bookmarks.py")
        if os.path.exists(make_script):
            print("Running make_fmhy_bookmarks.py to download latest sources and generate HTML files...")
            try:
                subprocess.run([sys.executable, make_script], check=True, cwd=ROOT_DIR)
                print("[SUCCESS] Bookmarks regenerated successfully.\n")
            except Exception as e:
                print(f"[WARNING] Failed to run make_fmhy_bookmarks.py: {e}")
                
    if not os.path.exists(source_path):
        print(f"[ERROR] Bookmark source file not found at: {source_path}")
        sys.exit(1)
        
    # 2. Parse new FMHY bookmarks HTML
    print(f"\nParsing {source_file}...")
    new_root_folder_base = parse_bookmarks_html(source_path)
    
    # 3. Resolve profiles to update
    profiles_to_update = []
    if config and config.get("profiles"):
        for p in config["profiles"]:
            profiles_to_update.append({
                "browser": p["browser"],
                "type": p.get("type", "firefox" if p.get("bookmarks_file_path", "").endswith(".sqlite") else "chromium"),
                "profile_dir": p["profile_dir"],
                "profile_name": p["profile_name"],
                "bookmarks_file_path": p["bookmarks_file_path"]
            })
    else:
        # Scan system automatically
        all_profiles = find_browser_profiles()
        selected = select_profile(all_profiles)
        if selected:
            profiles_to_update.append({
                "browser": selected["browser"],
                "type": selected.get("type", "firefox" if selected.get("path", "").endswith(".sqlite") else "chromium"),
                "profile_dir": selected["profile_dir"],
                "profile_name": selected["profile_name"],
                "bookmarks_file_path": selected["path"]
            })

    any_success = False
    print(f"\nFound {len(profiles_to_update)} profile(s) to update.")
    
    # 4. Process each profile
    for idx, p_conf in enumerate(profiles_to_update):
        browser_name = p_conf["browser"]
        profile_name = p_conf["profile_name"]
        profile_dir_name = p_conf["profile_dir"]
        bookmarks_file_path = p_conf["bookmarks_file_path"]
        profile_type = p_conf.get("type", "firefox" if bookmarks_file_path.endswith(".sqlite") else "chromium")
        profile_dir = os.path.dirname(bookmarks_file_path)
        
        print(f"\n==============================================")
        print(f" [{idx + 1}/{len(profiles_to_update)}] Syncing {browser_name} - {profile_name}")
        print(f"==============================================")
        print(f"Target path: {bookmarks_file_path}")
        
        # Check and close browser
        success = check_and_close_browser(browser_name, non_interactive)
        if not success:
            print(f"[INFO] Skipping sync for {browser_name} - {profile_name} because the browser is running.")
            continue
            
        # Parse new bookmarks - deep copy from base to avoid sharing object references
        new_root_folder = copy.deepcopy(new_root_folder_base)
        
        safe_profile_dir = re.sub(r'[^a-zA-Z0-9_]', '_', profile_dir_name)
        profile_backup_dir = os.path.join(BACKUPS_DIR, browser_name, safe_profile_dir)
        os.makedirs(profile_backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if profile_type == "firefox":
            # Firefox update via SQLite places.sqlite
            backup_sqlite = os.path.join(profile_backup_dir, f"places_Backup_{timestamp}.sqlite")
            try:
                rel_sqlite_path = os.path.relpath(backup_sqlite, SCRIPT_DIR)
            except ValueError:
                rel_sqlite_path = f"backups/{browser_name}/{safe_profile_dir}/places_Backup_{timestamp}.sqlite"
                
            print(f"Creating SQLite backup to: {rel_sqlite_path}")
            shutil.copy2(bookmarks_file_path, backup_sqlite)
            
            # Export HTML backup
            try:
                existing_firefox_data = read_firefox_bookmarks_as_dict(bookmarks_file_path)
                html_backup_file = os.path.join(profile_backup_dir, f"Bookmarks_Backup_{timestamp}.html")
                save_backup_html(existing_firefox_data, html_backup_file)
            except Exception as e:
                print(f"[WARNING] Could not export HTML backup for Firefox: {e}")
                
            print("Writing updated FMHY folder to Firefox places.sqlite database...")
            try:
                update_firefox_places_sqlite(bookmarks_file_path, new_root_folder)
                print(f"[SUCCESS] {browser_name}'s bookmarks synced successfully!")
                any_success = True
            except Exception as e:
                print(f"[ERROR] Failed to update Firefox places.sqlite database: {e}")
                print("Restoring SQLite backup...")
                shutil.copy2(backup_sqlite, bookmarks_file_path)
                
        else:
            # Chromium update via Bookmarks JSON
            print("Reading browser bookmarks...")
            try:
                with open(bookmarks_file_path, "r", encoding="utf-8") as f:
                    bookmarks_data = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to read browser Bookmarks file: {e}")
                continue
                
            backup_bookmarks = os.path.join(profile_backup_dir, f"Bookmarks_Backup_{timestamp}.json")
            try:
                rel_json_path = os.path.relpath(backup_bookmarks, SCRIPT_DIR)
            except ValueError:
                rel_json_path = f"backups/{browser_name}/{safe_profile_dir}/Bookmarks_Backup_{timestamp}.json"
                
            print(f"Creating JSON backup to: {rel_json_path}")
            shutil.copy2(bookmarks_file_path, backup_bookmarks)
            
            # Create HTML Backup of original browser bookmarks
            html_backup_file = os.path.join(profile_backup_dir, f"Bookmarks_Backup_{timestamp}.html")
            save_backup_html(bookmarks_data, html_backup_file)
            
            bookmarks_bak_file = os.path.join(profile_dir, "Bookmarks.bak")
            if os.path.exists(bookmarks_bak_file):
                backup_bak = f"{bookmarks_bak_file}.{timestamp}.bak"
                shutil.copy2(bookmarks_bak_file, backup_bak)
                try:
                    os.remove(bookmarks_bak_file)
                except Exception as e:
                    print(f"[WARNING] Failed to remove Bookmarks.bak: {e}")
                    
            # Remove all existing FMHY folders anywhere
            removed_nodes = []
            for root_name in ["bookmark_bar", "other", "synced"]:
                if root_name in bookmarks_data.get("roots", {}):
                    res = remove_all_folders_named(bookmarks_data["roots"][root_name], "FMHY")
                    removed_nodes.extend(res)
                    
            if removed_nodes:
                print(f"Removed {len(removed_nodes)} existing FMHY folder(s) found in bookmarks.")
                removed_node = removed_nodes[0]
            else:
                print("No existing FMHY folder found.")
                removed_node = None
                
            # Always insert the new FMHY folder at the very front (index 0) of the Bookmarks bar
            if "bookmark_bar" not in bookmarks_data["roots"]:
                bookmarks_data["roots"]["bookmark_bar"] = {
                    "children": [],
                    "name": "Bookmarks bar",
                    "type": "folder"
                }
            
            print("Inserting updated FMHY folder at the front of Bookmarks bar...")
            bookmarks_data["roots"]["bookmark_bar"]["children"].insert(0, new_root_folder)
                
            # Collect IDs and assign new ones
            existing_ids = set()
            for root_name in ["bookmark_bar", "other", "synced"]:
                if root_name in bookmarks_data["roots"]:
                    collect_ids(bookmarks_data["roots"][root_name], existing_ids)
                    
            numeric_ids = []
            for id_str in existing_ids:
                try:
                    numeric_ids.append(int(id_str))
                except ValueError:
                    pass
                    
            max_id = max(numeric_ids) if numeric_ids else 0
            next_id_list = [max_id + 1]
            
            # Chrome epoch time: microseconds since Jan 1, 1601
            chrome_time = str(int((time.time() + 11644473600) * 1000000))
            
            # Preserve original metadata of root folder if available
            if removed_node:
                new_root_folder["id"] = removed_node["id"]
                new_root_folder["guid"] = removed_node["guid"]
                new_root_folder["date_added"] = removed_node.get("date_added", chrome_time)
                new_root_folder["date_modified"] = chrome_time
            else:
                new_root_folder["id"] = str(next_id_list[0])
                next_id_list[0] += 1
                new_root_folder["guid"] = str(uuid.uuid4())
                new_root_folder["date_added"] = chrome_time
                new_root_folder["date_modified"] = chrome_time
                
            # Prepare all inner children recursively
            prepare_nodes_for_chromium(new_root_folder["children"], next_id_list, chrome_time)
            
            # Remove the checksum key from top-level
            if "checksum" in bookmarks_data:
                del bookmarks_data["checksum"]
                
            # Write the updated bookmarks JSON to file
            print("Writing updated bookmarks file...")
            try:
                with open(bookmarks_file_path, "w", encoding="utf-8") as f:
                    json.dump(bookmarks_data, f, indent=4, ensure_ascii=False)
                print(f"[SUCCESS] {browser_name}'s bookmarks synced successfully!")
                any_success = True
                
                # Relaunch the browser (only in interactive mode!)
                if not non_interactive:
                    exe_path = find_browser_executable(browser_name)
                    if exe_path:
                        print(f"Launching {browser_name} with profile '{profile_dir_name}'...")
                        subprocess.Popen([exe_path, f"--profile-directory={profile_dir_name}"])
                    else:
                        print(f"Please launch your browser manually to see changes.")
            except Exception as e:
                print(f"[ERROR] Failed to write updated bookmarks file: {e}")
                print("Restoring backup...")
                shutil.copy2(backup_bookmarks, bookmarks_file_path)

if __name__ == "__main__":
    main()
