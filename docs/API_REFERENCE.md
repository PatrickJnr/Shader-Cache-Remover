# API Reference - Shader Cache Remover

## Core Services

### DetectionService

Service for locating shader cache directories across different platforms and applications.

#### Constructor
```python
DetectionService(custom_paths: Optional[List[Path]] = None)
```

#### Methods

##### `get_all_shader_cache_directories() -> List[Path]`
Returns a comprehensive list of all shader cache directories found across all platforms.

**Returns**: List of Path objects pointing to shader cache directories

**Example**:
```python
service = DetectionService()
directories = service.get_all_shader_cache_directories()
for directory in directories:
    print(f"Found cache: {directory}")
```

##### `get_steam_shader_caches() -> List[Path]`
Detects Steam shader cache directories.

**Returns**: List of Steam shader cache directory paths

##### `get_system_shader_caches() -> List[Path]`
Detects system-level shader cache directories (DirectX, Vulkan, etc.).

**Returns**: List of system shader cache directory paths

##### `get_custom_shader_caches() -> List[Path]`
Returns user-defined custom shader cache paths.

**Returns**: List of custom directory paths from configuration

### CleanupService

Service for safely removing shader cache files with progress tracking and statistics.

#### Constructor
```python
CleanupService(backup_service: BackupService)
```

#### Methods

##### `cleanup_directories(directories, dry_run=False, progress_callback=None) -> CleanupStats`
Main cleanup method with comprehensive tracking and safety features.

**Parameters**:
- `directories` (List[Path]): Directories to clean
- `dry_run` (bool): If True, only scan without deleting
- `progress_callback` (Callable): Function to call with progress updates

**Returns**: CleanupStats object with operation results

**Example**:
```python
def progress_update(progress: float):
    print(f"Progress: {progress}%")

stats = cleanup_service.cleanup_directories(
    directories,
    dry_run=False,
    progress_callback=progress_update
)
print(f"Cleaned {stats.files_deleted} files, freed {stats.bytes_freed} bytes")
```

##### `stop_cleanup() -> None`
Stops an ongoing cleanup operation.

### BackupService

Service for creating and managing shader cache backups.

#### Constructor
```python
BackupService()
```

#### Methods

##### `create_backup(source_paths, destination=None) -> bool`
Creates a backup of specified directories.

**Parameters**:
- `source_paths` (List[Path]): Directories to backup
- `destination` (Optional[Path]): Backup destination (uses configured location if None)

**Returns**: True if backup successful

**Example**:
```python
backup_service = BackupService()
success = backup_service.create_backup(
    shader_directories,
    Path("/custom/backup/location")
)
```

##### `set_backup_root(root_path) -> None`
Sets the root directory for automatic backups.

**Parameters**:
- `root_path` (Path): Base directory for backups

## Infrastructure Services

### ConfigManager

Configuration management service with persistent storage.

#### Constructor
```python
ConfigManager()
```

#### Methods

##### `is_auto_backup_enabled() -> bool`
Checks if automatic backup is enabled.

**Returns**: True if auto-backup is enabled

##### `get_backup_location() -> Path`
Gets the configured backup location.

**Returns**: Path object for backup directory

##### `get_custom_paths() -> List[Path]`
Gets user-defined custom shader cache paths.

**Returns**: List of custom directory paths

##### `should_show_progress() -> bool`
Checks if progress bar should be displayed.

**Returns**: True if progress display is enabled

##### `is_detailed_logging_enabled() -> bool`
Checks if detailed logging is enabled.

**Returns**: True if detailed logging is enabled

### LoggingConfig

Logging configuration and management service.

#### Constructor
```python
LoggingConfig(log_level: str = "INFO", detailed: bool = False)
```

#### Methods

##### `setup_logging(log_to_file=False) -> None`
Configures logging system.

**Parameters**:
- `log_to_file` (bool): Whether to log to file in addition to console

##### `get_logger(name) -> Logger`
Gets a configured logger instance.

**Parameters**:
- `name` (str): Logger name

**Returns**: Logger instance

##### `create_queue_handler(queue) -> Handler`
Creates a queue handler for GUI logging.

**Parameters**:
- `queue` (Queue): Queue for log messages

**Returns**: QueueHandler instance

## GUI Components

### MainWindow

Main application window with complete UI management.

#### Constructor
```python
MainWindow(root: tk.Tk)
```

#### Key Attributes
- `root` (tk.Tk): Root tkinter window
- `config_manager` (ConfigManager): Configuration service
- `detection_service` (DetectionService): Cache detection service
- `cleanup_service` (CleanupService): Cleanup service
- `backup_service` (BackupService): Backup service
- `colors` (dict): Catppuccin color palette

#### Color Palette
The application uses the Catppuccin Mocha color scheme:

```python
colors = {
    "base": "#0a0a1a",      # Main background
    "surface0": "#16162e",   # Secondary background
    "surface1": "#242444",   # Tertiary background
    "text": "#f0f0ff",       # Main text color
    "pink": "#f2c2e7",       # Accent color (progress bar)
    "mauve": "#cba6f7",      # Secondary accent
    # ... additional colors
}
```

## Data Structures

### CleanupStats
Statistics from cleanup operations.

#### Attributes
- `files_deleted` (int): Number of files deleted
- `directories_deleted` (int): Number of directories deleted
- `bytes_freed` (int): Total bytes freed
- `errors` (int): Number of errors encountered
- `start_time` (datetime): Operation start time
- `end_time` (datetime): Operation end time

#### Methods
- `get_duration() -> timedelta`: Get operation duration
- `get_files_per_second() -> float`: Get processing rate

## Exception Handling

### Custom Exceptions
The application defines several custom exceptions for better error handling:

#### ShaderCacheError
Base exception for shader cache operations.

#### DetectionError
Raised when shader cache detection fails.

#### CleanupError
Raised when cleanup operations fail.

#### BackupError
Raised when backup operations fail.

### Error Handling Patterns
```python
try:
    directories = detection_service.get_all_shader_cache_directories()
except DetectionError as e:
    logger.error(f"Detection failed: {e}")
    # Handle error gracefully
```

## Threading and Concurrency

### Main Thread Operations
- GUI updates must occur on main thread
- Use `root.after()` for UI updates from background threads

### Background Operations
- File operations run in separate threads
- Progress updates marshaled to main thread
- Proper thread cleanup on application exit

### Example: Thread-Safe Progress Updates
```python
def progress_callback(progress: float):
    # This runs in background thread
    root.after(0, lambda: update_progress_ui(progress))

def update_progress_ui(progress: float):
    # This runs on main thread
    progress_var.set(progress)
    draw_progress_bar(progress)
```

## Configuration File Format

### JSON Schema
```json
{
  "version": "1.0",
  "auto_backup": {
    "enabled": true,
    "location": "/path/to/backups"
  },
  "custom_paths": [
    "/custom/shader/cache/path"
  ],
  "ui_settings": {
    "show_progress": true,
    "detailed_logging": false
  }
}
```

## Performance Considerations

### Memory Management
- Large directory trees processed in chunks
- Progress callbacks batched for efficiency
- Proper cleanup of temporary resources

### CPU Usage
- File operations optimized for I/O efficiency
- Progress updates throttled to avoid UI overhead
- Background threads use appropriate priorities

## Testing Interfaces

### Mock Services
For testing, services can be mocked or replaced:

```python
# Example test setup
mock_detection = MockDetectionService()
mock_backup = MockBackupService()

cleanup_service = CleanupService(mock_backup)
directories = mock_detection.get_directories()
```

## Integration Points

### External Dependencies
- **tkinter** - GUI framework (usually included with Python)
- **pathlib** - Path manipulation (Python 3.4+)
- **logging** - Logging framework (standard library)

### Optional Dependencies
- **psutil** - Enhanced process management (optional)
- **pywin32** - Windows-specific features (Windows only)

## Security Considerations

### File Operations
- Path validation before file operations
- Safe handling of permission errors
- No execution of external commands
- Read-only operations where possible

### User Input
- Validation of custom paths
- Sanitization of configuration values
- Safe error message display

## Troubleshooting API

### Debug Mode
Enable detailed logging for troubleshooting:

```python
logging_config = LoggingConfig(log_level="DEBUG", detailed=True)
logging_config.setup_logging()
```

### Service Inspection
Check service state for debugging:

```python
# Inspect detection service
print(f"Custom paths: {detection_service.custom_paths}")
print(f"Steam paths: {detection_service.steam_paths}")

# Check cleanup service state
print(f"Backup service configured: {cleanup_service.backup_service is not None}")
```

## Examples

### Basic Usage
```python
from shader_cache_remover.core.detection_service import DetectionService
from shader_cache_remover.core.cleanup_service import CleanupService
from shader_cache_remover.core.backup_service import BackupService

# Initialize services
detection = DetectionService()
backup = BackupService()
cleanup = CleanupService(backup)

# Find shader caches
directories = detection.get_all_shader_cache_directories()
print(f"Found {len(directories)} shader cache directories")

# Cleanup with progress tracking
def on_progress(progress):
    print(f"Progress: {progress:.1f}%")

stats = cleanup.cleanup_directories(
    directories,
    dry_run=True,
    progress_callback=on_progress
)

print(f"Would delete {stats.files_deleted} files")
```

### GUI Integration
```python
import tkinter as tk
from shader_cache_remover.gui.main_window import MainWindow

# Create GUI application
root = tk.Tk()
app = MainWindow(root)
root.mainloop()
```

### Configuration Management
```python
from shader_cache_remover.infrastructure.config_manager import ConfigManager

config = ConfigManager()

# Check settings
if config.is_auto_backup_enabled():
    backup_location = config.get_backup_location()
    print(f"Backups will be saved to: {backup_location}")

# Get custom paths
custom_paths = config.get_custom_paths()
for path in custom_paths:
    print(f"Custom path: {path}")
