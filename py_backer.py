import time
import os
import shutil
import json
import sys
import platform
from pathlib import Path
import re

backer_ver = "1.2"

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        print(f"Error creating directory {directory}: {e}")
        return False

def normalize_path(path_str):
    """Normalize path for current operating system"""
    if not path_str:
        return ""
    
    # Convert to Path object and resolve
    path = Path(path_str).expanduser().resolve()
    return str(path)

def parse_version(version_str):
    """Parse version string and return components (major, minor, patch, build)"""
    try:
        # Match version format x.y.z.w
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)$', version_str.strip())
        if match:
            return [int(x) for x in match.groups()]
        else:
            # If not in expected format, try to add missing parts
            parts = version_str.split('.')
            while len(parts) < 4:
                parts.append('0')
            return [int(x) for x in parts[:4]]
    except (ValueError, AttributeError):
        print(f"Warning: Invalid version format '{version_str}'. Using default 1.0.0.0")
        return [1, 0, 0, 0]

def increment_build_number(version_components):
    """Increment the build number (4th component) and return new version"""
    version_components[3] += 1
    return '.'.join(map(str, version_components))

def create_versioned_backup_path(base_backup_dir, project_name, project_version):
    """Create versioned backup directory path"""
    version_folder = f"{project_name}_v{project_version}"
    return os.path.join(base_backup_dir, version_folder)

def update_config_version(config_file_path, new_version):
    """Update the project version in the config file"""
    try:
        # Read current config
        with open(config_file_path, "r", encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Update version
        config_data["project_version"] = new_version
        
        # Write back to file
        with open(config_file_path, "w", encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        
        return True
    except (OSError, PermissionError, json.JSONDecodeError) as e:
        print(f"Error updating config file: {e}")
        return False

def copy_item(item_path, backup_dir):
    """Copy file or directory to backup location"""
    try:
        # Ensure backup directory exists
        if not ensure_directory_exists(backup_dir):
            return False
            
        item_name = os.path.basename(item_path)
        destination = os.path.join(backup_dir, item_name)
        
        if os.path.isdir(item_path):
            # Recursively copy the directory
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(item_path, destination)
        else:
            shutil.copy2(item_path, destination)
        return True
    except (OSError, PermissionError, shutil.Error) as e:
        print(f"Error copying {item_path} to {backup_dir}: {e}")
        return False

def normalize_excluded_paths(excluded_dirs_dict, source_dirs):
    """Normalize and organize excluded paths by source directory index"""
    excluded_by_index = {}
    
    for index_str, excluded_paths in excluded_dirs_dict.items():
        try:
            index = int(index_str)
            if index < len(source_dirs):
                source_dir = normalize_path(source_dirs[index])
                
                # Convert excluded paths string to list if needed
                if isinstance(excluded_paths, str):
                    excluded_list = [excluded_paths]
                else:
                    excluded_list = excluded_paths
                
                normalized_excluded = []
                for excluded_path in excluded_list:
                    excluded_path = excluded_path.strip()
                    if not excluded_path:
                        continue
                        
                    # Handle both absolute and relative paths
                    if os.path.isabs(excluded_path):
                        # Absolute path - normalize it
                        normalized_excluded.append(normalize_path(excluded_path))
                    else:
                        # Relative path - make it relative to source directory
                        full_excluded_path = os.path.join(source_dir, excluded_path)
                        normalized_excluded.append(normalize_path(full_excluded_path))
                
                excluded_by_index[index] = normalized_excluded
        except (ValueError, IndexError):
            print(f"Warning: Invalid excluded_dirs index '{index_str}'. Skipping.")
    
    return excluded_by_index

def is_path_excluded(path, excluded_paths):
    """Check if a path should be excluded based on the exclusion list"""
    if not excluded_paths:
        return False
    
    normalized_path = normalize_path(path)
    
    for excluded_path in excluded_paths:
        # Check for exact match
        if normalized_path == excluded_path:
            return True
        
        # Check if the path is a subdirectory of an excluded path
        try:
            rel_path = os.path.relpath(normalized_path, excluded_path)
            if not rel_path.startswith('..'):
                return True
        except ValueError:
            # Can happen on Windows when paths are on different drives
            continue
    
    return False

def validate_directories(source_dirs, backup_dirs, excluded_by_index):
    """Validate that source directories exist and backup directories can be created"""
    valid_pairs = []
    
    for i, (source_dir, backup_dir) in enumerate(zip(source_dirs, backup_dirs)):
        source_dir = normalize_path(source_dir)
        backup_dir = normalize_path(backup_dir)
        
        if not source_dir or not backup_dir:
            print(f"Warning: Empty path in configuration for index {i}. Skipping.")
            continue
            
        if not os.path.exists(source_dir):
            print(f"Warning: Source directory does not exist: {source_dir}. Skipping.")
            continue
            
        if not os.path.isdir(source_dir):
            print(f"Warning: Source path is not a directory: {source_dir}. Skipping.")
            continue
            
        # Try to create base backup directory (not the versioned one yet)
        if not ensure_directory_exists(backup_dir):
            print(f"Warning: Cannot create backup directory: {backup_dir}. Skipping.")
            continue
        
        # Show excluded paths for this source directory
        excluded_paths = excluded_by_index.get(i, [])
        if excluded_paths:
            print(f"✓ Monitoring: {source_dir} -> {backup_dir}")
            print(f"  Excluded paths ({len(excluded_paths)}):")
            for excluded in excluded_paths:
                rel_excluded = os.path.relpath(excluded, source_dir) if excluded.startswith(source_dir) else excluded
                print(f"    - {rel_excluded}")
        else:
            print(f"✓ Monitoring: {source_dir} -> {backup_dir}")
            
        valid_pairs.append((source_dir, backup_dir, i))
    
    return valid_pairs

def monitor_directories(source_dirs, backup_dirs, backup_times, excluded_by_index, project_name, project_version, config_file_path):
    """Monitor directories for changes and backup when detected"""
    # Validate directories first
    valid_pairs = validate_directories(source_dirs, backup_dirs, excluded_by_index)
    
    if not valid_pairs:
        print("Error: No valid directory pairs found. Please check your configuration.")
        return
    
    print(f"\nStarting monitoring of {len(valid_pairs)} directory pairs...")
    print("Press Ctrl+C to stop monitoring.\n")
    
    # Initialize tracking dictionaries
    item_mod_times = {}
    last_backup_times = {}
    
    # Parse initial version
    version_components = parse_version(project_version)
    current_version = '.'.join(map(str, version_components))
    
    for source_dir, backup_dir, index in valid_pairs:
        item_mod_times[source_dir] = {}
        last_backup_times[source_dir] = 0

    try:
        while True:
            current_time = time.time()
            changes_detected = False
            
            for source_dir, backup_dir, index in valid_pairs:
                delay = int(backup_times.get(str(index), 5))  # default to 5 seconds
                excluded_paths = excluded_by_index.get(index, [])
                
                if current_time - last_backup_times[source_dir] >= delay:
                    backup_needed = False
                    changed_items = []
                    
                    try:
                        for root, dirs, files in os.walk(source_dir):
                            # Check if current root directory should be excluded
                            if is_path_excluded(root, excluded_paths):
                                # Skip this directory and all its subdirectories
                                dirs.clear()  # This prevents os.walk from descending into subdirs
                                continue
                            
                            # Filter out excluded directories from dirs list to prevent descent
                            dirs_to_remove = []
                            for dir_name in dirs:
                                dir_path = os.path.join(root, dir_name)
                                if is_path_excluded(dir_path, excluded_paths):
                                    dirs_to_remove.append(dir_name)
                            
                            for dir_name in dirs_to_remove:
                                dirs.remove(dir_name)
                            
                            # Process files and remaining directories
                            for name in dirs + files:
                                item_path = os.path.join(root, name)
                                
                                # Double-check exclusion for individual items
                                if is_path_excluded(item_path, excluded_paths):
                                    continue
                                
                                if not os.path.exists(item_path):
                                    continue
                                    
                                rel_path = os.path.relpath(item_path, source_dir)
                                
                                try:
                                    current_mod_time = os.path.getmtime(item_path)
                                except (OSError, PermissionError):
                                    continue
                                
                                # Check if the item is modified or new
                                if current_mod_time != item_mod_times[source_dir].get(item_path, 0):
                                    item_mod_times[source_dir][item_path] = current_mod_time
                                    changed_items.append((item_path, rel_path))
                                    backup_needed = True
                    
                    except (OSError, PermissionError) as e:
                        print(f"Error accessing source directory {source_dir}: {e}")
                    
                    # If changes detected, increment version and perform backup
                    if backup_needed and changed_items:
                        # Increment build number
                        version_components = parse_version(current_version)
                        new_version = increment_build_number(version_components)
                        
                        # Create versioned backup directory
                        versioned_backup_dir = create_versioned_backup_path(backup_dir, project_name, new_version)
                        
                        print(f"\n🔄 Changes detected! Creating backup v{new_version}")
                        print(f"Backup location: {versioned_backup_dir}")
                        
                        # Show excluded items count if any were skipped
                        if excluded_paths:
                            print(f"Note: {len(excluded_paths)} exclusion rule(s) active for this source")
                        
                        # Perform backup for all changed items
                        backup_success = True
                        for item_path, rel_path in changed_items:
                            backup_item_path = os.path.join(versioned_backup_dir, rel_path)
                            backup_parent_dir = os.path.dirname(backup_item_path)
                            
                            if copy_item(item_path, backup_parent_dir):
                                print(f"  ✓ Backed up: {rel_path}")
                            else:
                                print(f"  ❌ Failed to backup: {rel_path}")
                                backup_success = False
                        
                        # Update config file with new version if backup was successful
                        if backup_success:
                            if update_config_version(config_file_path, new_version):
                                current_version = new_version
                                print(f"  ✓ Updated project version to {new_version}")
                                changes_detected = True
                            else:
                                print(f"  ⚠️  Backup completed but failed to update config file")
                        else:
                            print(f"  ⚠️  Some items failed to backup, version not updated")
                        
                        print()  # Empty line for readability
                    
                    last_backup_times[source_dir] = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

def load_config():
    """Load configuration from config.json file"""
    config_file = "config.json"
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Please create a config.json file with your directory settings.")
        return None, None
    
    try:
        with open(config_file, "r", encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing config.json: {e}")
        return None, None
    except (OSError, PermissionError) as e:
        print(f"Error reading config.json: {e}")
        return None, None
    
    return config_data, config_file

if __name__ == "__main__":
    print(f"PyBacker {backer_ver}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print("-" * 50)
    
    config_data, config_file_path = load_config()
    if config_data is None:
        sys.exit(1)
    
    # Extract configuration
    proj_name = config_data.get("project_name", "Unknown Project")
    proj_ver = config_data.get("project_version", "1.0.0.0")
    
    source_dirs_dict = config_data.get("source_dirs", {})
    backup_dirs_dict = config_data.get("backup_dirs", {})
    excluded_dirs_dict = config_data.get("excluded_dirs", {})
    backup_times = config_data.get("backup_times", {})
    
    # Convert to lists, preserving order
    max_index = max(
        max((int(k) for k in source_dirs_dict.keys()), default=-1),
        max((int(k) for k in backup_dirs_dict.keys()), default=-1)
    )
    
    source_dirs = []
    backup_dirs = []
    
    for i in range(max_index + 1):
        source_dir = source_dirs_dict.get(str(i), "")
        backup_dir = backup_dirs_dict.get(str(i), "")
        
        if source_dir and backup_dir:  # Only add if both paths exist
            source_dirs.append(source_dir)
            backup_dirs.append(backup_dir)
    
    if not source_dirs or not backup_dirs:
        print("Error: No valid source/backup directory pairs found in configuration.")
        sys.exit(1)
    
    # Process excluded directories
    excluded_by_index = normalize_excluded_paths(excluded_dirs_dict, source_dirs)
    
    print(f"Project: {proj_name} v{proj_ver}")
    print(f"Found {len(source_dirs)} directory pairs in configuration.")
    if excluded_by_index:
        total_exclusions = sum(len(paths) for paths in excluded_by_index.values())
        print(f"Found {total_exclusions} exclusion rules across {len(excluded_by_index)} source directories.")
    print("Versioned backups will be created for each change detection.")
    print()
    
    monitor_directories(source_dirs, backup_dirs, backup_times, excluded_by_index, proj_name, proj_ver, config_file_path)