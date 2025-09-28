# User Guide - Shader Cache Remover

## Quick Start

1. **Launch the application**
   ```bash
   python -m shader_cache_remover.gui.main_window
   ```

2. **Choose your operation**:
   - **Start Cleanup** - Remove shader cache files
   - **Dry Run** - Preview what would be deleted
   - **Backup Shaders** - Create backup before cleanup

3. **Monitor progress** - Watch the real-time progress bar and activity log

4. **Review results** - Check the statistics and log output

## Interface Overview

### Main Window
- **Title Bar** - Application name and settings button
- **Progress Section** - Visual progress bar and percentage
- **Action Buttons** - Start, Dry Run, Backup, and Stop operations
- **Activity Log** - Real-time log of operations
- **Statistics Bar** - Files processed, space freed, errors, timing

### Settings Dialog
Access via the ⚙️ button in the top-right corner:
- **Auto-backup** - Automatically create backups before cleanup
- **Custom paths** - Add additional directories to scan
- **Progress display** - Show/hide progress bar
- **Detailed logging** - Enable verbose logging

## Operation Modes

### Start Cleanup
- **Deletes shader cache files** from detected directories
- **Creates backup** if auto-backup is enabled
- **Shows detailed progress** with file counts and space freed
- **Logs all operations** with timestamps

### Dry Run
- **Scans directories** without deleting files
- **Shows what would be deleted** in the log
- **Safe preview mode** - no files are modified
- **Useful for verification** before actual cleanup

### Backup Only
- **Creates backup** of current shader cache files
- **User selects backup location**
- **Preserves file structure** in backup
- **Timestamped backup names** for organization

## Understanding the Log

### Log Levels
- **INFO** (Blue) - General information and progress
- **WARNING** (Yellow) - Non-critical issues
- **ERROR** (Red) - Critical errors that need attention
- **DEBUG** (Gray) - Detailed technical information

### Common Log Messages
```
INFO: Found 15 shader cache directories to process
INFO: Processing shader cache in: /path/to/game/shadercache
INFO: Would delete: file1.cache (1.2 MB)
INFO: Cleanup completed. Summary: 150 files deleted. Total space freed: 6.7 GB
```

## Best Practices

### Before First Use
1. **Run a Dry Run** to see what will be deleted
2. **Enable auto-backup** in settings
3. **Review custom paths** if you have specific directories

### Regular Maintenance
1. **Backup important game saves** before cleanup
2. **Run cleanup monthly** or when experiencing performance issues
3. **Monitor disk space** to track effectiveness

### Troubleshooting
1. **Check the activity log** for error messages
2. **Verify paths** in settings if no caches are found
3. **Run dry run first** if unsure about operations

## Performance Tips

- **Close games** before running cleanup for best results
- **Run during low system activity** for faster processing
- **Use dry run** to estimate cleanup time
- **Enable detailed logging** only when debugging issues

## Safety Features

- **Dry run mode** - Preview without deletion
- **Backup creation** - Automatic backups before cleanup
- **Progress tracking** - Real-time monitoring of operations
- **Error handling** - Graceful handling of file system issues
- **Confirmation dialogs** - Prevents accidental operations

## Common Issues

### No Shader Caches Found
- Check if games are installed
- Verify Steam/Epic Games paths
- Add custom paths in settings
- Run as administrator if needed

### Slow Performance
- Close other applications
- Clean temporary files first
- Check disk space availability
- Consider excluding large directories

### Permission Errors
- Run as administrator
- Check file permissions
- Close applications using the files
- Verify antivirus exclusions
