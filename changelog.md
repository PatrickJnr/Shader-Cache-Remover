# Changelog

## [1.4.0] - 13-07-2025

### Added
- **Enhanced User Interface**: Complete GUI overhaul with a modern dark theme and improved layout.
- **Real-time Progress Tracking**: Added a progress bar with live updates during cleanup operations.
- **Comprehensive Statistics**: Real-time display of files deleted, directories removed, bytes freed, errors, and elapsed time.
- **Settings System**: Configurable settings with persistent storage in a JSON file.
- **Auto-backup Feature**: Optional automatic backup before cleanup with a configurable backup location.
- **Stop Functionality**: Ability to cancel cleanup operations in progress.
- **Status Updates**: Real-time status messages showing the current operation's progress.
- **Configuration Management**: Settings stored in the user's home directory with auto-loading/saving.
- **Enhanced Logging**: Timestamped and color-coded log entries with improved formatting and visibility controls.
- **Cross-platform Compatibility**: Improved drive detection for Windows and Unix-like systems.
- **Additional Shader Cache Locations**: Support for Intel shader cache, AMD GLCache, and custom user-defined paths.
- **Better Error Reporting**: Comprehensive error counting and detailed error messages in the log.
- **Thread Safety**: Proper thread management with daemon threads and clean shutdown procedures.
- **Window Close Handling**: Safe application exit with confirmation if a cleanup is in progress.
- **Human-readable File Sizes**: Automatic formatting of byte values to KB/MB/GB/TB.
- **Custom Path Support**: Ability to add, edit, and validate custom shader cache directories through the settings menu.

### Changed
- **Code Architecture**: Complete refactoring with better separation of concerns, type hints, and the use of dataclasses.
- **Button Layout**: Improved button arrangement with a better visual hierarchy and clear actions.
- **Logging System**: Enhanced logging with queue-based message processing for improved thread safety.
- **Directory Processing**: More robust directory traversal with better error handling.
- **Internal Method Naming**: Renamed internal methods for clarity and to resolve critical naming conflicts (e.g., `start_dry_run`).
- **Backup System**: Enhanced backup functionality with better directory structure preservation and error handling.
- **Dry Run Implementation**: Improved dry run mode with accurate item counting and preview logging.

### Improved
- **Performance**: Optimized directory scanning and file operations.
- **User Experience**: A more intuitive interface with clear feedback and status updates. The settings window is now a proper modal dialog, improving workflow.
- **Reliability**: Enhanced robustness by preventing the duplicate processing of the same cache directory.
- **Safety**: Improved graceful application shutdown, even when a cleanup process is active.
- **Resource Management**: More reliable management of resources, such as ensuring Windows registry keys are always closed properly.
- **Error Handling**: Increased resilience against file system errors (e.g., a file being deleted by an external process during cleanup).
- **Code Quality**: Added type hints, dataclasses, and better documentation for improved maintainability.

### Fixed
- **Critical Button Functionality**: Resolved a major bug where the 'Dry Run' and 'Backup Shaders' buttons did not work correctly due to a method naming conflict.
- **UI Freezing**: Eliminated GUI freezing during long operations by correctly managing background threads and UI updates.
- **Dialog Box Behavior**: Ensured that dialog boxes (e.g., for file selection or warnings) correctly appear on top of the settings window.
- **Registry Access**: Implemented safer handling of Windows registry access to prevent errors and ensure resource cleanup.
- **Path Handling**: Improved cross-platform path management and validation of custom paths.
- **Error Propagation**: Corrected error reporting from background threads to the main UI and logs.
- **Progress Accuracy**: Refined progress and statistics display logic for better accuracy at the beginning and end of operations.

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