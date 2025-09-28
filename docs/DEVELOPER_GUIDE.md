# Developer Guide - Shader Cache Remover

## Architecture Overview

The application follows a modular architecture with clear separation of concerns:

```
shader_cache_remover/
├── core/                 # Core business logic
│   ├── detection_service.py    # Directory and file detection
│   ├── cleanup_service.py      # File deletion and processing
│   └── backup_service.py       # Backup creation and management
├── infrastructure/       # Supporting infrastructure
│   ├── config_manager.py       # Configuration management
│   ├── logging_config.py       # Logging setup and handlers
│   └── registry_utils.py       # Windows registry utilities
├── gui/                  # User interface components
│   ├── main_window.py          # Main application window
│   ├── settings_dialog.py      # Settings and configuration UI
│   └── widgets/               # Reusable UI components
├── services/             # Additional services
└── utils/               # Utility functions and helpers
```

## Core Components

### DetectionService
**Responsibility**: Locate shader cache directories across different platforms

**Key Methods**:
- `get_all_shader_cache_directories()` - Main entry point for detection
- `get_steam_shader_caches()` - Steam-specific cache detection
- `get_system_shader_caches()` - System-level cache detection
- `get_custom_shader_caches()` - User-defined custom paths

**Detection Logic**:
```python
def get_all_shader_cache_directories(self) -> List[Path]:
    """Aggregate all shader cache directories from different sources."""
    directories = []

    # Steam detection
    directories.extend(self.get_steam_shader_caches())

    # System detection
    directories.extend(self.get_system_shader_caches())

    # Custom paths
    directories.extend(self.get_custom_shader_caches())

    return directories
```

### CleanupService
**Responsibility**: Safely remove shader cache files with progress tracking

**Key Features**:
- Progress callback support
- Dry run capability
- Error handling and recovery
- Statistics tracking

**Main Interface**:
```python
def cleanup_directories(
    self,
    directories: List[Path],
    dry_run: bool = False,
    progress_callback: Optional[Callable] = None
) -> CleanupStats:
    """Clean shader cache directories with comprehensive tracking."""
```

### BackupService
**Responsibility**: Create and manage file backups

**Key Methods**:
- `create_backup()` - Create backup of specified directories
- `set_backup_root()` - Configure backup destination
- `get_backup_path()` - Generate timestamped backup paths

## GUI Architecture

### MainWindow Class
**Central UI Component**: Manages the entire application interface

**Key Responsibilities**:
- Window layout and styling
- Event handling and coordination
- Service initialization and management
- Theme application and consistency

**Color Scheme**: Catppuccin Mocha palette for modern appearance

### Custom Progress Bar
**Challenge**: System-level ttk.Progressbar styling limitations
**Solution**: Custom Canvas-based progress bar with full color control

**Implementation**:
```python
def _draw_custom_progress_bar(self, percentage: float):
    """Custom progress bar drawing with full color control."""
    # Canvas-based implementation for complete styling control
    canvas_width = self.progress_canvas.winfo_width() or 500
    progress_width = (percentage / 100) * canvas_width

    # Draw background and progress fill with custom colors
    self.progress_canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                        fill=self.colors["surface0"])
    self.progress_canvas.create_rectangle(0, 0, progress_width, canvas_height,
                                        fill=self.colors["pink"])
```

## Configuration System

### ConfigManager
**Storage**: JSON-based configuration with versioning
**Scope**: User preferences, custom paths, UI settings

**Key Configuration Areas**:
- Auto-backup settings
- Custom search paths
- UI preferences (progress bar visibility, logging level)
- Performance settings

### Settings Dialog
**Interface**: Tabbed dialog for comprehensive configuration
**Validation**: Real-time validation of paths and settings
**Persistence**: Automatic saving and loading of preferences

## Error Handling Strategy

### Comprehensive Error Management
1. **File System Errors** - Permission issues, missing directories
2. **Configuration Errors** - Invalid paths, corrupted settings
3. **Service Errors** - Network issues, unavailable resources
4. **UI Errors** - Rendering issues, threading problems

### Error Recovery
- Graceful degradation when non-critical features fail
- User-friendly error messages with actionable guidance
- Automatic retry mechanisms for transient failures
- Comprehensive logging for debugging

## Threading Model

### Background Operations
- **Cleanup Thread** - Non-blocking file operations
- **Progress Updates** - Thread-safe UI updates via `root.after()`
- **Logging Thread** - Asynchronous log message processing

### Thread Safety
- All UI updates queued through main thread
- Shared data structures protected with proper synchronization
- Service state managed through controlled interfaces

## Testing Strategy

### Unit Tests
- Individual service testing
- Utility function validation
- Configuration management testing

### Integration Tests
- Full workflow testing
- UI interaction validation
- Error condition handling

### Test Structure
```
tests/
├── unit/
│   ├── test_detection_service.py
│   ├── test_cleanup_service.py
│   └── test_config_manager.py
├── integration/
│   ├── test_gui_workflow.py
│   └── test_backup_restore.py
└── fixtures/
    └── sample_shader_caches/
```

## Performance Considerations

### Optimization Strategies
- **Lazy Loading** - Services initialized only when needed
- **Progress Batching** - Efficient progress updates
- **Memory Management** - Proper cleanup of resources
- **Caching** - Configuration and path caching

### Monitoring
- **Progress Tracking** - Real-time operation monitoring
- **Resource Usage** - Memory and CPU monitoring
- **Performance Metrics** - Operation timing and statistics

## Deployment

### Package Structure
```
setup.py                  # Package configuration
requirements.txt          # Dependencies
MANIFEST.in              # Package contents
shader_cache_remover/     # Main package
docs/                     # Documentation
tests/                    # Test suite
```

### Installation Modes
- **Development** - Editable install for active development
- **Production** - Standard install for end users
- **Portable** - Single-directory deployment

## Contributing Guidelines

### Code Standards
- **PEP 8** - Python style guide compliance
- **Type Hints** - Comprehensive type annotations
- **Documentation** - Docstrings for all public interfaces
- **Testing** - Test coverage for new features

### Development Workflow
1. **Feature Branch** - Isolate changes in dedicated branches
2. **Testing** - Comprehensive test coverage
3. **Code Review** - Peer review process
4. **Documentation** - Update relevant documentation
5. **Integration** - Merge and validate integration

## API Reference

### Service Interfaces

#### DetectionService
```python
class DetectionService:
    def get_all_shader_cache_directories(self) -> List[Path]: ...
    def get_steam_shader_caches(self) -> List[Path]: ...
    def get_system_shader_caches(self) -> List[Path]: ...
```

#### CleanupService
```python
class CleanupService:
    def cleanup_directories(self, directories: List[Path],
                          dry_run: bool = False,
                          progress_callback: Optional[Callable] = None) -> CleanupStats: ...
```

#### BackupService
```python
class BackupService:
    def create_backup(self, source_paths: List[Path],
                     destination: Optional[Path] = None) -> bool: ...
```

### Configuration Interfaces

#### ConfigManager
```python
class ConfigManager:
    def is_auto_backup_enabled(self) -> bool: ...
    def get_backup_location(self) -> Path: ...
    def get_custom_paths(self) -> List[Path]: ...
```

## Troubleshooting Development Issues

### Common Development Problems
1. **Import Errors** - Check package structure and imports
2. **GUI Freezing** - Ensure proper thread handling
3. **Styling Issues** - Verify color definitions and application
4. **Path Problems** - Validate path handling across platforms

### Debug Mode
- Enable detailed logging
- Use debug breakpoints
- Check service initialization order
- Validate configuration loading
