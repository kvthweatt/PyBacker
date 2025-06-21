# PyBacker - Intelligent File Backup System

A cross-platform, real-time file monitoring and backup system with intelligent versioning, cascade detection, and exclusion support.

## Features

- **Real-time Monitoring**: Continuously monitors multiple source directories for changes
- **Cross-Platform**: Works seamlessly on Windows, Linux, and macOS
- **Intelligent Versioning**: Automatic version incrementing with configurable thresholds
- **Cascade Detection**: Handles backup-of-backup scenarios with single version increments
- **Exclusion Support**: Skip directories like `node_modules`, `.git`, build outputs, etc.
- **Versioned Backups**: Each backup creates a new versioned folder for complete history
- **Persistent State**: Resumes from last version number after restarts

## Version System

PyBacker uses a sophisticated 4-component version system: `Major.Minor.Patch.Build`

### Version Progression
- **Build** increments with every backup
- **Patch** increments every `next_alpha` builds (resets build to 0)
- **Minor** increments every `next_beta` patches (resets patch to 0)  
- **Major** increments every `next_major` minors (resets minor to 0)

### Example with Default Thresholds
```
next_alpha: 250    (patch every 250 builds)
next_beta: 4       (minor every 4 patches)
next_major: 3      (major every 3 minors)

Result: Major version increments every 3,000 builds (250 × 4 × 3)
```

## Installation

1. Ensure Python 3.6+ is installed
2. Download `py_backer.py`
3. Create a `config.json` file (see configuration section)
4. Run: `python py_backer.py`

## Configuration

Create a `config.json` file in the same directory as `py_backer.py`:

```json
{
    "project_name": "MyProject",
    "project_version": "1.0.0.0",
    
    "next_alpha": "250",
    "next_beta": "4",
    "next_major": "3",
    
    "source_dirs": {
        "0": "~/Documents/MyProject",
        "1": "~/Documents/AnotherProject",
        "2": "C:/Work/ImportantFiles"
    },
    
    "backup_dirs": {
        "0": "~/Backups/MyProject",
        "1": "~/Backups/AnotherProject", 
        "2": "D:/Backups/ImportantFiles"
    },
    
    "excluded_dirs": {
        "0": ["node_modules", ".git", "build", "dist"],
        "1": "target",
        "2": ["temp", "cache", "logs"]
    },
    
    "backup_times": {
        "0": "120",
        "1": "60", 
        "2": "0"
    }
}
```

### Configuration Options

| Field | Description | Example |
|-------|-------------|---------|
| `project_name` | Name of your project | `"MyProject"` |
| `project_version` | Starting version (auto-updated) | `"1.0.0.0"` |
| `next_alpha` | Builds before patch increment | `"250"` |
| `next_beta` | Patches before minor increment | `"4"` |
| `next_major` | Minors before major increment | `"3"` |
| `source_dirs` | Directories to monitor | `{"0": "~/Documents/Project"}` |
| `backup_dirs` | Where to store backups | `{"0": "~/Backups/Project"}` |
| `excluded_dirs` | Paths to skip | `{"0": ["node_modules", ".git"]}` |
| `backup_times` | Scan delay in seconds (`"0"` = immediate) | `{"0": "120"}` |

### Path Formats

**Cross-Platform Support:**
- `~/Documents/Project` (home directory)
- `/home/user/project` (Linux absolute)
- `C:/Users/User/Project` (Windows with forward slashes)
- `C:\\Users\\User\\Project` (Windows with backslashes)

**Exclusion Formats:**
- Single string: `"node_modules"`
- Array: `["node_modules", ".git", "build"]`
- Relative paths: `"src/temp"`
- Absolute paths: `"/full/path/to/exclude"`

## Backup Structure

Each backup creates a versioned folder:

```
~/Backups/MyProject/
├── MyProject_v1.0.0.1/
│   ├── [backed up files]
├── MyProject_v1.0.0.2/
│   ├── [backed up files]
├── MyProject_v1.0.1.0/    ← Patch increment
│   ├── [backed up files]
└── MyProject_v1.1.0.0/    ← Minor increment
    ├── [backed up files]
```

## Advanced Features

### Cascade Detection

Perfect for backup-of-backup scenarios:

```json
{
    "source_dirs": {
        "0": "~/Work/Project",
        "1": "~/Backups/Project"
    },
    "backup_dirs": {
        "0": "~/Backups/Project", 
        "1": "~/OfflineBackups/Project"
    }
}
```

When `~/Work/Project` changes:
1. Backs up to `~/Backups/Project`
2. Detects `~/Backups/Project` has new content  
3. Immediately backs up to `~/OfflineBackups/Project`
4. **Single version increment** for the entire cascade

### Common Exclusions

```json
{
    "excluded_dirs": {
        "0": [
            "node_modules",     // JavaScript dependencies
            ".git",             // Git repository
            ".svn",             // SVN repository
            "__pycache__",      // Python cache
            "target",           // Rust/Java builds
            "build",            // Build outputs
            "dist",             // Distribution files
            ".vscode",          // VS Code settings
            ".idea",            // IntelliJ settings
            "temp",             // Temporary files
            "logs",             // Log files
            "cache"             // Cache directories
        ]
    }
}
```

## Usage Examples

### Basic Monitoring
```bash
python py_backer.py
```

### Output Example
```
PyBacker 1.2
Platform: Linux 5.15.0
Python: 3.9.7
--------------------------------------------------
Project: MyProject v1.0.0.5
Found 2 directory pairs in configuration.
Found 4 exclusion rules across 1 source directories.
Version progression: Patch every 250 builds, Minor every 1000 builds, Major every 3000 builds

✓ Monitoring: /home/user/Documents/MyProject -> /home/user/Backups/MyProject
  Excluded paths (4):
    - node_modules
    - .git
    - build
    - temp

Starting monitoring of 2 directory pairs...
Version thresholds: Patch every 250 builds, Minor every 4 patches, Major every 3 minors
Press Ctrl+C to stop monitoring.

🔄 Changes detected! 1.0.0.5 → 1.0.0.6 (🔄 BUILD)
Progress: 6/250 builds to next patch (244 remaining)

Backup location: /home/user/Backups/MyProject/MyProject_v1.0.0.6

  ✓ /home/user/Documents/MyProject: src/main.py
  ✓ /home/user/Documents/MyProject: README.md

  ✓ Updated project version to 1.0.0.6
  ✓ Backed up 1 source(s) to 1 destination(s)
```

## Version History Tracking

The system maintains complete version history:
- Each backup gets a unique version number
- Version increments persist across restarts
- Complete project timeline preserved in separate folders
- Easy rollback to any previous version

## Error Handling

- **Missing directories**: Automatically creates backup directories
- **Permission errors**: Gracefully skips inaccessible files
- **Config errors**: Clear error messages with suggestions
- **Crash recovery**: Resumes from last successful backup version

## Performance

- **Efficient scanning**: Only processes changed files
- **Smart exclusions**: Skips directories entirely, including subdirectories
- **Minimal overhead**: Uses modification time checking
- **Cascade optimization**: Detects backup-induced changes immediately

## Requirements

- Python 3.6 or higher
- Standard library only (no external dependencies)
- Read/write access to source and backup directories

## Troubleshooting

### Common Issues

**"No valid directory pairs found"**
- Check that source directories exist
- Verify backup directories can be created
- Ensure proper JSON formatting in config.json

**"Permission denied"**
- Run with appropriate permissions
- Check file/folder ownership
- Ensure backup destinations are writable

**"Version not updating"**
- Check config.json is writable
- Verify JSON syntax is valid
- Look for backup operation failures

### Debug Tips

1. Start with simple configuration (1-2 directories)
2. Use immediate backup timing (`"0"`) for testing
3. Check console output for specific error messages
4. Verify paths are correct for your operating system

## License

This project is provided as-is for personal and commercial use.