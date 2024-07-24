# Changelog

## [1.3.0] - 25-07-2024

### Added
- **Recursive Directory Cleaning**: Enhanced the script to check for shader caches in nested subdirectories for comprehensive cleanup.
- **Backup Option**: Added an option to create backups of directories containing shader cache files before deletion.
- **Dry Run Mode**: Implemented a dry run mode that simulates the cleanup process without deleting any files, allowing users to review what would be removed.
- **Enhanced Logging**: Improved logging to include information about directories found, files deleted, and actions taken.

## [1.2.0] - 14-07-2024

### Added
- Additional logging messages to provide more detailed user feedback during the cleanup process.
- Detailed docstrings to enhance code documentation and readability.

### Changed
- Optimized directory traversal for larger directories by logging before processing each directory.
- Enhanced error handling to catch and log specific exceptions (`FileNotFoundError`, `PermissionError`) separately.

### Removed
- Redundant and unspecific exception handling, replaced with more targeted exception handling.

## [1.1.0] - 21-05-2024

### Added
- Switched from using `os.path` to `pathlib.Path` for path manipulations.
- Replaced `print` statements with the `logging` module for better logging control.
- Enhanced function docstrings to provide more detailed documentation.
- Added type annotations to function signatures for better type checking and readability.

### Changed
- Improved error handling to be more specific and detailed.

### Removed
- Removed redundant `os.path.exists()` and `os.path.join()` calls by utilizing `pathlib.Path` features.
- Removed direct `os` module imports in favor of `pathlib`.

## [1.0.0] - 19-05-2024

### Features
- Function to remove all files and directories in a specified directory using `os.path`.
- Function to remove shader cache from known locations on Windows 11 using `os.path`.
- Basic error handling and logging using `print` statements.