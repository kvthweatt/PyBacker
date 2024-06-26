# PyBacker
A simple, lightweight backup daemon written in Python to help you maintain files in the event they are lost or deleted on accident.

You can set a backup directory as a source directory to create a backup chain for double/triple/... backups.

Written to operate on Windows systems.

## Configuring PyBacker
You will notice inside the config.json there are source and destination directories with numeric key values that increment.
Each numeric key of a source directory path corresponds to the destination directory path with the same key.
You can add an unlimited amount of sources/destinations.
- You must be sure to have an equal number of sources and destinations because the key indexes are related to each other, otherwise, PyBacker will crash.

## To-Do:
- Add command line args for CLI operation and a GUI.
- Add the ability to backup over FTP / SFTP

## Changelog
- v1.3 Updated to perform recursive directory backup and display an error for any failed items.
- v1.2 Updated to support backup times to allow for staggered backups.
- v1.1 Updated to support multiple backup directories
- v1.0 base release
