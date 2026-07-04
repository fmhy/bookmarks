#!/usr/bin/env python3
"""Interactive configuration tool to select browser profiles and generate sync settings."""

import os
import sys
import json

# Define standard search paths for browser profiles on Windows
def scan_browser_profiles():
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
            # Scan for profiles containing a Bookmarks and Preferences file
            for item in os.listdir(user_data_path):
                profile_path = os.path.join(user_data_path, item)
                if os.path.isdir(profile_path):
                    bookmarks_file = os.path.join(profile_path, "Bookmarks")
                    preferences_file = os.path.join(profile_path, "Preferences")
                    if os.path.exists(bookmarks_file):
                        # Extract profile name and email if Preferences exists
                        friendly_name = None
                        email = None
                        if os.path.exists(preferences_file):
                            try:
                                with open(preferences_file, 'r', encoding='utf-8') as f:
                                    pref_data = json.load(f)
                                
                                # 1. Get profile name
                                friendly_name = pref_data.get('profile', {}).get('name')
                                
                                # 2. Get email from account_info
                                accounts = pref_data.get('account_info', [])
                                if accounts and isinstance(accounts, list):
                                    email = accounts[0].get('email')
                                    
                                # Fallback email locations
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

def main():
    print("====================================================")
    print("      FMHY Bookmarks Sync - Configuration Tool")
    print("====================================================\n")
    
    profiles = scan_browser_profiles()
    if not profiles:
        print("[ERROR] No browser profiles found automatically on your system.")
        print("Please ensure Google Chrome, Brave, or Microsoft Edge is installed.")
        sys.exit(1)
        
    print("Available Browser Profiles:")
    for idx, p in enumerate(profiles):
        display_name = p['profile_name']
        details = []
        if p['email']:
            details.append(p['email'])
        if p['profile_dir'] != display_name:
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
