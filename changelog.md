# Changelog

## [1.1.0] - 2024-05-21

### Changed
- Switched from using `os.path` to `pathlib.Path` for path manipulations.
- Replaced `print` statements with the `logging` module for better logging control.
- Enhanced function docstrings to provide more detailed documentation.
- Added type annotations to function signatures for better type checking and readability.
- Improved error handling to be more specific and detailed.

### Removed
- Removed redundant `os.path.exists()` and `os.path.join()` calls by utilizing `pathlib.Path` features.
- Removed direct `os` module imports in favor of `pathlib`.

## [1.0.0] - 2024-05-19

### Features
- Function to remove all files and directories in a specified directory using `os.path`.
- Function to remove shader cache from known locations on Windows 11 using `os.path`.
- Basic error handling and logging using `print` statements.
