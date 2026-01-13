# Changelog

## [1.6.0] - 13-01-2026

### Architecture Improvements & GUI Modernization

#### Added
- **Cache Provider Plugin System**: Extensible provider architecture for cache detection
  - 12 built-in providers: NVIDIA, AMD, Intel, Steam, Epic Games, GOG Galaxy, EA App, Unreal Engine, Unity, System, Browser Cache, Custom
  - Per-provider enable/disable configuration
  - Priority-based detection ordering
- **4 New Cache Providers**
  - Epic Games Launcher (webcache, downloads)
  - GOG Galaxy (webcache, storage)
  - EA App/Origin (cache directories)
  - Browser Cache (Chrome, Edge, Firefox, Brave, Opera GPU caches)
- **UI Improvements**
  - Collapsible "Cache Providers" section with per-provider checkboxes
  - Confirmation dialog showing locations, estimated size, providers before cleanup
  - Export Report button - saves cleanup stats and log to text file
  - Restore button - restore from previous backups
  - History button - view past cleanup operations
- **Restore from Backup**
  - New `RestoreDialog` for selecting and restoring backups
  - `BackupService.list_backups()` and `restore_backup()` methods
  - Shows backup date, size, and file count
- **Cleanup History Tracking**
  - `HistoryService` with JSON persistence (~/.shader_cache_remover_history.json)
  - Records: timestamp, files, dirs, bytes, duration, providers used
  - `HistoryDialog` showing all past cleanups with aggregate stats
- **System Integration**
  - `NotificationService` for Windows toast notifications (win10toast/plyer)
  - `SchedulerService` for Windows Task Scheduler integration
  - Optional dependencies in pyproject.toml: `pip install .[full]`
- **Cancellation Tokens**: Thread-safe cooperative cancellation replacing boolean flags
- **Centralized Deletion Gate**: Safety checks blocking system paths (Windows, Program Files)
- **Pre-flight Validation Service**: Permission and disk space checks before cleanup
- **Filesystem Abstraction**: `RealFileSystem` and `MockFileSystem` for testability
- **Config Versioning**: Automatic migration support with `_version` field
- **Modern pyproject.toml**: Replaced setup.py with hatchling build system

#### Changed
- **GUI Theme**: Replaced Catppuccin with Windows Fluent-inspired dark theme
  - Neutral dark background (#1a1a1a)
  - Windows blue accent (#0078d4)
  - Semantic button colors (green/blue/orange/red)
  - Cleaner card-based layout
- **Code Reduction**: main_window.py (991->580 lines), settings_dialog.py (922->340 lines)
- **DetectionService**: Refactored to use provider registry pattern
- Progress bar now properly resizes when window is resized
- Progress bar fills full width at 100% completion

#### Improved
- **Safety**: All deletions route through DeletionGate with absolute blocklist
- **Testability**: MockFileSystem enables unit testing without real file operations
- **Extensibility**: Custom providers can be registered at runtime
- **Maintainability**: Cleaner separation between interfaces and implementations

### New Core Modules
```
shader_cache_remover/core/
├── interfaces.py         # CacheProvider protocol, CacheLocation, CacheType
├── cancellation.py       # CancellationToken, CancellationTokenSource
├── deletion_gate.py      # Centralized safety gate for deletions
├── validation_service.py # Pre-flight validation checks
├── history_service.py    # Cleanup history tracking
└── providers/            # Cache detection providers
    ├── nvidia.py, amd.py, intel.py
    ├── steam.py, epic.py, gog.py, ea.py
    ├── unreal.py, unity.py, browser.py
    ├── system.py, custom.py
    └── base.py           # BaseCacheProvider abstract class

shader_cache_remover/gui/
├── restore_dialog.py     # Restore from backup dialog
└── history_dialog.py     # Cleanup history dialog

shader_cache_remover/infrastructure/
├── notifications.py      # Windows toast notifications
└── scheduler.py          # Task Scheduler integration
```

---

## [1.5.0] - 28-09-2025

### Major Architecture Overhaul - Modular Refactoring

#### Added
- **Complete Modular Architecture**: Transformed monolithic 1000+ line script into clean, maintainable modules
- **Core Services Layer**: Dedicated business logic modules for detection, cleanup, and backup operations
- **Infrastructure Layer**: Supporting services for configuration, logging, and system integration
- **GUI Components**: Modular interface components with proper separation of concerns
- **Comprehensive Test Suite**: Automated testing with 4/4 test coverage validation
- **Package Configuration**: Proper Python package setup with entry points and dependencies
- **Dual Logging System**: Simultaneous console and GUI logging for enhanced debugging
- **Single Entry Point**: Clean, unified application entry point with backward compatibility

#### Changed
- **Architecture**: Complete refactoring from procedural to modular object-oriented design
- **Code Organization**: Separated concerns into logical modules (core, infrastructure, gui)
- **Import System**: Implemented proper absolute imports for better maintainability
- **Error Handling**: Enhanced exception handling with graceful degradation
- **Logging Strategy**: Dual-output logging to both console and GUI interfaces

#### Improved
- **Maintainability**: Each module can be modified independently without affecting others
- **Testability**: Services can be unit tested in isolation
- **Extensibility**: Easy to add new cache detection methods and features
- **Debugging**: Better error isolation and comprehensive logging
- **Code Quality**: Type hints, proper documentation, and clean interfaces
- **Performance**: Optimized module loading and service initialization

#### Fixed
- **Import Issues**: Resolved relative import problems with proper package structure
- **Entry Point Confusion**: Eliminated duplicate main files with single clear entry point
- **Logging Duplication**: Fixed logging to appear in both console and GUI as intended
- **Module Dependencies**: Corrected circular import issues and dependency management

### New Modular Structure
```
shader_cache_remover/
├── core/                    # Business logic services
│   ├── detection_service.py    # Shader cache directory detection
│   ├── cleanup_service.py      # File and directory removal
│   └── backup_service.py       # Backup operations
├── infrastructure/          # Supporting services
│   ├── config_manager.py       # Configuration management
│   ├── registry_utils.py       # Windows registry operations
│   └── logging_config.py       # Centralized logging
├── gui/                     # User interface components
│   ├── main_window.py          # Main application window
│   └── settings_dialog.py      # Settings management dialog
├── main.py                  # Application entry point
└── setup.py                 # Package configuration
```

### Technical Improvements
- **Dependency Injection**: Proper service initialization and dependency management
- **Configuration Management**: Centralized settings with validation and persistence
- **Registry Integration**: Safe Windows registry operations with error handling
- **Thread Safety**: Improved thread management for GUI responsiveness
- **Resource Management**: Proper cleanup of system resources and file handles

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
