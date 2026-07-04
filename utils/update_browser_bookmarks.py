#!/usr/bin/env python3
"""Update local browser bookmarks (Brave, Chrome, Edge) with FMHY bookmarks."""

import os
import sys
import re
import json
import uuid
import time
import shutil
import subprocess
import copy
from datetime import datetime

# Path resolution relative to script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
BACKUPS_DIR = os.path.join(SCRIPT_DIR, "backups")

# Define standard search paths for browser profiles on Windows
def find_browser_profiles():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []
        
    browsers = {
        "Brave": os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data"),
        "Chrome": os.path.join(local_app_data, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(local_app_data, "Microsoft", "Edge", "User Data")
    }
    
    profiles = []
    for browser_name, user_data_path in browsers.items():
        if os.path.exists(user_data_path):
            # Scan for profiles containing a Bookmarks file
            for item in os.listdir(user_data_path):
                profile_path = os.path.join(user_data_path, item)
                if os.path.isdir(profile_path):
                    bookmarks_file = os.path.join(profile_path, "Bookmarks")
                    preferences_file = os.path.join(profile_path, "Preferences")
                    if os.path.exists(bookmarks_file):
                        # Try to resolve friendly name and email
                        friendly_name = None
                        email = None
                        if os.path.exists(preferences_file):
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
                            "profile_dir": item,
                            "profile_name": friendly_name or item,
                            "email": email,
                            "path": bookmarks_file,
                            "dir": profile_path
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
        
    for path in search_paths:
        if os.path.exists(path):
            return path
    return None

def is_browser_running(browser_name):
    executable_map = {
        "Brave": "brave.exe",
        "Chrome": "chrome.exe",
        "Edge": "msedge.exe"
    }
    exe_name = executable_map.get(browser_name)
    if not exe_name:
        return False
        
    try:
        output = subprocess.check_output("tasklist", shell=True, text=True, errors="ignore")
        return exe_name.lower() in output.lower()
    except Exception:
        return False

def check_and_close_browser(browser_name, non_interactive=False):
    executable_map = {
        "Brave": "brave.exe",
        "Chrome": "chrome.exe",
        "Edge": "msedge.exe"
    }
    exe_name = executable_map.get(browser_name)
    if not exe_name:
        return True
        
    if is_browser_running(browser_name):
        if non_interactive:
            # Safe skip for background tasks
            print(f"[INFO] {browser_name} is currently running. Skipping sync to avoid closing active tabs.")
            return False
            
        while is_browser_running(browser_name):
            print(f"\n[WARNING] {browser_name} is currently running!")
            print("Modifying bookmarks while the browser is running will result in changes being overwritten.")
            choice = input(f"Would you like to force close {browser_name} now? (y/n) or press Enter after closing it manually: ").strip().lower()
            if choice == 'y':
                try:
                    print(f"Closing {browser_name}...")
                    subprocess.run(["taskkill", "/f", "/im", exe_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(1.5)
                except Exception as e:
                    print(f"Failed to close browser: {e}. Please close it manually.")
            else:
                print("Press Enter to verify if the browser is closed...")
                input()
    return True

def select_profile(profiles):
    if not profiles:
        print("No browser profiles found automatically.")
        path = input("Please enter the absolute path to your browser's 'Bookmarks' file: ").strip()
        if not path:
            print("No path entered. Exiting.")
            sys.exit(1)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            sys.exit(1)
        return {
            "browser": "Custom",
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

    lines = content.splitlines()
    root_nodes = []
    stack = []
    
    folder_re = re.compile(r'<DT><H3>(.*?)</H3>')
    link_re = re.compile(r'<DT><A HREF="(.*?)"[^>]*>(.*?)</A>')
    dl_re = re.compile(r'<DL><p>')
    end_dl_re = re.compile(r'</DL><p>')
    
    skipped_levels = 0
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        folder_match = folder_re.search(line_stripped)
        if folder_match:
            folder_name = folder_match.group(1)
            if folder_name == "/":
                skipped_levels += 1
            else:
                new_folder = {
                    "type": "folder",
                    "name": folder_name,
                    "children": []
                }
                stack.append(new_folder)
            continue
            
        if dl_re.search(line_stripped):
            continue
            
        if end_dl_re.search(line_stripped):
            if skipped_levels > 0:
                skipped_levels -= 1
            else:
                if stack:
                    completed_folder = stack.pop()
                    if stack:
                        stack[-1]["children"].append(completed_folder)
                    else:
                        root_nodes.append(completed_folder)
            continue
            
        link_match = link_re.search(line_stripped)
        if link_match:
            url, name = link_match.groups()
            new_bookmark = {
                "type": "url",
                "name": name,
                "url": url
            }
            if stack:
                stack[-1]["children"].append(new_bookmark)
            else:
                root_nodes.append(new_bookmark)
            continue
            
    return root_nodes

def collect_ids(node, ids_set):
    if "id" in node:
        ids_set.add(node["id"])
    if "children" in node:
        for child in node["children"]:
            collect_ids(child, ids_set)

def prepare_nodes_for_chromium(nodes, next_id_list, chrome_time):
    for node in nodes:
        node["id"] = str(next_id_list[0])
        next_id_list[0] += 1
        node["guid"] = str(uuid.uuid4())
        node["date_added"] = chrome_time
        
        if node["type"] == "folder":
            node["date_modified"] = chrome_time
            if "children" not in node:
                node["children"] = []
            prepare_nodes_for_chromium(node["children"], next_id_list, chrome_time)

def remove_all_folders_named(node, target_name):
    """Recursively searches for and removes all folder nodes named target_name."""
    removed_nodes = []
    if "children" in node:
        i = 0
        while i < len(node["children"]):
            child = node["children"][i]
            if child.get("type") == "folder" and child.get("name") == target_name:
                removed_nodes.append(node["children"].pop(i))
                continue
            
            # Recurse
            res = remove_all_folders_named(child, target_name)
            if res:
                removed_nodes.extend(res)
            i += 1
    return removed_nodes

def export_bookmarks_to_html(node, file_handle, indent=0):
    """Recursively writes Chromium bookmark nodes to Netscape HTML format."""
    spaces = "    " * indent
    if node.get("type") == "folder":
        name = node.get("name", "Folder")
        if indent > 0:
            file_handle.write(f'{spaces}<DT><H3 ADD_DATE="{node.get("date_added", "0")}" LAST_MODIFIED="{node.get("date_modified", "0")}">{name}</H3>\n')
            file_handle.write(f'{spaces}<DL><p>\n')
        
        for child in node.get("children", []):
            export_bookmarks_to_html(child, file_handle, indent + 1)
            
        if indent > 0:
            file_handle.write(f'{spaces}</DL><p>\n')
    elif node.get("type") == "url":
        url = node.get("url", "")
        name = node.get("name", "Bookmark")
        file_handle.write(f'{spaces}<DT><A HREF="{url}" ADD_DATE="{node.get("date_added", "0")}">{name}</A>\n')

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
                    # Print root children
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

def main():
    non_interactive = "--non-interactive" in sys.argv
    
    print("====================================================")
    print("  Chromium Bookmarks Automatic Updater (FMHY)")
    print("====================================================\n")
    
    config = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"[INFO] Loaded config containing {len(config.get('profiles', []))} profiles")
        except Exception as e:
            print(f"[WARNING] Failed to load config.json: {e}")



    # 1. Fetch & Rebuild Source File if needed
    rebuild = False
    if config:
        rebuild = config.get("rebuild_first", True)
    else:
        if not non_interactive:
            rebuild_choice = input("Would you like to fetch the latest FMHY files and rebuild bookmarks first? (y/n) [default: y]: ").strip().lower()
            rebuild = False if rebuild_choice == 'n' else True
            
    if rebuild:
        print("Running make_fmhy_bookmarks.py to download latest sources and generate HTML files...")
        try:
            make_script = os.path.join(ROOT_DIR, "make_fmhy_bookmarks.py")
            subprocess.run([sys.executable, make_script], cwd=ROOT_DIR, check=True)
            print("[SUCCESS] Bookmarks regenerated successfully.\n")
        except Exception as e:
            print(f"[WARNING] Could not rebuild bookmarks automatically: {e}")
            print("Using existing local bookmark HTML files.\n")
            
    # 2. Select Source File
    source_file = None
    if config:
        source_file = os.path.join(ROOT_DIR, config.get("source_file", "fmhy_in_bookmarks.html"))
    else:
        html_files = []
        full_html = os.path.join(ROOT_DIR, "fmhy_in_bookmarks.html")
        starred_html = os.path.join(ROOT_DIR, "fmhy_in_bookmarks_starred_only.html")
        
        if os.path.exists(full_html):
            html_files.append(("Full Bookmarks (fmhy_in_bookmarks.html)", full_html))
        if os.path.exists(starred_html):
            html_files.append(("Starred-only Bookmarks (fmhy_in_bookmarks_starred_only.html)", starred_html))
            
        if not html_files:
            print("[ERROR] No generated bookmark HTML files found.")
            sys.exit(1)
            
        if len(html_files) == 1:
            source_file = html_files[0][1]
            print(f"Using bookmarks file: {os.path.basename(html_files[0][1])}")
        else:
            print("Select the bookmark source file to import:")
            for idx, (label, _) in enumerate(html_files):
                print(f"[{idx + 1}] {label}")
            try:
                choice = input(f"Choice (1-{len(html_files)}, default 1): ").strip()
                idx = int(choice) - 1 if choice else 0
                if 0 <= idx < len(html_files):
                    source_file = html_files[idx][1]
                else:
                    source_file = html_files[0][1]
            except Exception:
                source_file = html_files[0][1]
                
    # Parse new bookmarks once (source is common to all profiles)
    print(f"\nParsing {os.path.basename(source_file)}...")
    root_nodes = parse_bookmarks_html(source_file)
    if not root_nodes or root_nodes[0]["name"] != "FMHY":
        print("[ERROR] Failed to parse bookmarks folder correctly. Root folder should be 'FMHY'.")
        sys.exit(1)
        
    new_root_folder_base = root_nodes[0]

    # 3. Identify Browser Profiles to Update
    profiles_to_update = []
    if config and "profiles" in config:
        profiles_to_update = config["profiles"]
    else:
        # Interactive selection
        all_profiles = find_browser_profiles()
        if not all_profiles:
            print("[ERROR] No browser profiles found automatically.")
            sys.exit(1)
            
        print("\nAvailable Browser Profiles:")
        for idx, p in enumerate(all_profiles):
            display_name = p['profile_name']
            details = []
            if p['email']:
                details.append(p['email'])
            if p['profile_dir'] != display_name:
                details.append(p['profile_dir'])
            details_str = f" ({', '.join(details)})" if details else ""
            print(f"[{idx + 1}] {p['browser']} - {display_name}{details_str}")
            
        selected_profiles = []
        while True:
            choice = input(f"Select profile(s) to update (1-{len(all_profiles)}) [default 1]. Separate multiple with commas, or type 'all': ").strip()
            if not choice:
                selected_profiles = [all_profiles[0]]
                break
            elif choice.lower() == 'all':
                selected_profiles = all_profiles
                break
            
            parts = [p.strip() for p in choice.split(",") if p.strip()]
            valid = True
            temp_selected = []
            for p in parts:
                try:
                    idx = int(p) - 1
                    if 0 <= idx < len(all_profiles):
                        temp_selected.append(all_profiles[idx])
                    else:
                        print(f"[ERROR] Index {p} is out of bounds (1-{len(all_profiles)}).")
                        valid = False
                        break
                except ValueError:
                    print(f"[ERROR] '{p}' is not a valid number.")
                    valid = False
                    break
            
            if valid and temp_selected:
                selected_profiles = temp_selected
                break
        
        for p in selected_profiles:
            profiles_to_update.append({
                "browser": p["browser"],
                "profile_dir": p["profile_dir"],
                "profile_name": p["profile_name"],
                "bookmarks_file_path": p["path"]
            })

    any_success = False
    print(f"\nFound {len(profiles_to_update)} profile(s) to update.")
    
    # 4. Process each profile
    for idx, p_conf in enumerate(profiles_to_update):
        browser_name = p_conf["browser"]
        profile_name = p_conf["profile_name"]
        profile_dir_name = p_conf["profile_dir"]
        bookmarks_file_path = p_conf["bookmarks_file_path"]
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
        
        # Read browser Bookmarks
        print("Reading browser bookmarks...")
        try:
            with open(bookmarks_file_path, "r", encoding="utf-8") as f:
                bookmarks_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read browser Bookmarks file: {e}")
            continue
            
        # Backup files safely before writing in structured folders
        safe_profile_dir = re.sub(r'[^a-zA-Z0-9_]', '_', profile_dir_name)
        profile_backup_dir = os.path.join(BACKUPS_DIR, browser_name, safe_profile_dir)
        os.makedirs(profile_backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
            print(f"[SUCCESS] Bookmarks updated successfully for {browser_name} - {profile_name}!")
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
