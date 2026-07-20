#!/usr/bin/env python3
"""Interactive configuration tool to select browser profiles and generate sync settings."""

import os
import sys
import json

import shutil

def find_browser_executable(browser_name):
    """Locate the executable path for the specified browser on Windows."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    
    exe_map = {
        "Brave": ["brave.exe"],
        "Chrome": ["chrome.exe"],
        "Edge": ["msedge.exe"],
        "Vivaldi": ["vivaldi.exe"],
        "Opera": ["opera.exe", "launcher.exe"],
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
            os.path.join(program_files_x86, "Mozilla Firefox", "firefox.exe"),
            os.path.join(local_app_data, "Mozilla Firefox", "firefox.exe")
        ]
    elif browser_name == "Zen Browser":
        search_paths = [
            os.path.join(program_files, "Zen Browser", "zen.exe"),
            os.path.join(local_app_data, "zen", "zen.exe"),
            os.path.join(local_app_data, "Programs", "zen", "zen.exe")
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
            
    for exe in exe_map.get(browser_name, []):
        which_path = shutil.which(exe)
        if which_path and os.path.isfile(which_path):
            return which_path
            
    return None

def clean_profile_name(raw_name):
    if not raw_name:
        return "Default"
    lower = raw_name.lower()
    if lower in ("default-release", "default-nightly", "default", "default profile") or "default-release" in lower or lower.endswith(".default"):
        return "Default"
    return raw_name

# Define standard search paths for browser profiles on Windows
def scan_browser_profiles():
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

def main():
    print("====================================================")
    print("      FMHY Bookmarks Sync - Configuration Tool")
    print("====================================================\n")
    
    profiles = scan_browser_profiles()
    if not profiles:
        print("[ERROR] No browser profiles found automatically on your system.")
        print("Please ensure Google Chrome, Brave, Edge, or Firefox is installed.")
        sys.exit(1)
        
    print("Available Browser Profiles:")
    for idx, p in enumerate(profiles):
        display_name = p['profile_name']
        details = []
        if p['email']:
            details.append(p['email'])
        elif p['profile_dir'] != display_name and not p['profile_dir'].lower().endswith('.' + display_name.lower()):
            details.append(p['profile_dir'])
            
        details_str = f" ({', '.join(details)})" if details else ""
        print(f"[{idx + 1}] {p['browser']} - {display_name}{details_str}")
        
    print("")
    
    # 1. Profile selection
    selected_profiles = []
    while True:
        choice = input(f"Select profile(s) to update (1-{len(profiles)}) [default 1]. Separate multiple with commas, or type 'all': ").strip()
        if not choice:
            selected_profiles = [profiles[0]]
            break
        elif choice.lower() == 'all':
            selected_profiles = profiles
            break
        
        parts = [p.strip() for p in choice.split(",") if p.strip()]
        valid = True
        temp_selected = []
        for p in parts:
            try:
                idx = int(p) - 1
                if 0 <= idx < len(profiles):
                    temp_selected.append(profiles[idx])
                else:
                    print(f"[ERROR] Index {p} is out of bounds (1-{len(profiles)}).")
                    valid = False
                    break
            except ValueError:
                print(f"[ERROR] '{p}' is not a valid number.")
                valid = False
                break
        
        if valid and temp_selected:
            selected_profiles = temp_selected
            break
            
    print("\nSelected Profiles:")
    for p in selected_profiles:
        print(f"  - {p['browser']} (Profile: {p['profile_name']})")
    print("")
    
    # 2. Source file selection
    print("Select bookmark source to sync:")
    print("[1] Full Bookmarks (fmhy_in_bookmarks.html)")
    print("[2] Starred-only Bookmarks (fmhy_in_bookmarks_starred_only.html)")
    while True:
        source_choice = input("Choice (1-2) [default 1]: ").strip()
        if not source_choice or source_choice == '1':
            source_type = "full"
            source_file = "fmhy_in_bookmarks.html"
            break
        elif source_choice == '2':
            source_type = "starred"
            source_file = "fmhy_in_bookmarks_starred_only.html"
            break
        else:
            print("Invalid choice. Enter 1 or 2.")
            
    # 3. Auto-rebuild selection
    rebuild_choice = input("\nShould the script always download latest sources from GitHub and rebuild bookmarks before syncing? (y/n) [default: y]: ").strip().lower()
    rebuild = False if rebuild_choice == 'n' else True
    
    # Generate config dictionary
    profiles_config = []
    for p in selected_profiles:
        profiles_config.append({
            "browser": p["browser"],
            "type": p.get("type", "chromium"),
            "profile_dir": p["profile_dir"],
            "profile_name": p["profile_name"],
            "email": p["email"],
            "bookmarks_file_path": p["path"]
        })
        
    config = {
        "profiles": profiles_config,
        "source_type": source_type,
        "source_file": source_file,
        "rebuild_first": rebuild
    }
    
    # Ensure utils directory exists (it should, but just in case)
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        
    print(f"\n[SUCCESS] Configuration saved to {config_path}!")
    print(json.dumps(config, indent=4))
    print("\nYou can now run the sync tool hands-free.")

if __name__ == "__main__":
    main()
