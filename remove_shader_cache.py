import shutil
import logging
from pathlib import Path
import os
import argparse
import traceback
from logging.handlers import RotatingFileHandler

# Determine the directory of the script
script_directory = Path(__file__).parent

# Specify log file path in the same directory as the script
log_file_path = script_directory / 'shader_cache_cleanup.log'

# Configure logging with rotation
handler = RotatingFileHandler(log_file_path, maxBytes=5 * 1024 * 1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        handler,  # Rotating log file
        logging.StreamHandler()  # Log to console
    ]
)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Shader Cache Cleanup Tool")
    parser.add_argument('--dry-run', action='store_true', help="Run without deleting files")
    parser.add_argument('--backup', action='store_true', help="Create backups of directories before deletion")
    return parser.parse_args()

def backup_files_in_directory(directory: Path):
    """Backup all files in the specified directory to a backup location."""
    backup_directory = directory.parent / f"{directory.name}_backup"
    
    try:
        shutil.copytree(directory, backup_directory)
        logging.info(f"Backup created at: {backup_directory}")
    except Exception as e:
        logging.warning(f"Failed to create backup for {directory}. Reason: {e}")
        logging.error(traceback.format_exc())

def remove_files_in_directory(directory: Path, dry_run: bool):
    """Remove all files and directories in the specified directory."""
    if not directory.exists():
        logging.warning(f"Directory {directory} does not exist.")
        return

    for item in directory.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                if not dry_run:
                    item.unlink()
                logging.info(f"{'Would delete' if dry_run else 'Deleted'} file/symlink: {item}")
            elif item.is_dir():
                if not dry_run:
                    shutil.rmtree(item)
                logging.info(f"{'Would delete' if dry_run else 'Deleted'} directory: {item}")
        except FileNotFoundError:
            logging.error(f"File not found: {item}")
        except PermissionError:
            logging.error(f"Permission denied: {item}")
        except Exception as e:
            logging.error(f"Failed to delete {item}. Reason: {e}")
            logging.error(traceback.format_exc())

def remove_shader_cache(dry_run: bool, backup: bool):
    """Remove shader cache from known locations on Windows."""
    shader_cache_directories = [
        Path.home() / 'AppData' / 'Local' / 'NVIDIA' / 'DXCache',
        Path.home() / 'AppData' / 'Local' / 'NVIDIA' / 'GLCache',
        Path.home() / 'AppData' / 'Local' / 'AMD' / 'DxCache',
        Path.home() / 'AppData' / 'Local' / 'UnrealEngine' / 'ShaderCache',
        Path.home() / 'AppData' / 'LocalLow' / 'Unity' / 'Caches',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'NVIDIA Corporation' / 'NV_Cache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'DXCache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'D3DSCache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'AMD' / 'GLCache',
        Path.home() / 'AppData' / 'Roaming' / 'Unreal Engine' / 'Common' / 'DerivedDataCache',
        Path.home() / 'AppData' / 'Roaming' / 'Unity' / 'Asset Store-5.x',
        Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'CLR_v4.0',
    ]

    found_directories = []

    for directory in shader_cache_directories:
        if directory.exists() and any(directory.iterdir()):
            found_directories.append(directory)
            logging.info(f"Found shader cache in directory: {directory}")
            
            if backup:
                backup_files_in_directory(directory)
                
            # Remove files and directories recursively
            remove_files_in_directory(directory, dry_run)

            # Check for nested directories
            for subdirectory in directory.rglob('*'):
                if subdirectory.is_dir():  # Check if it's a directory
                    if not dry_run:
                        shutil.rmtree(subdirectory)
                    logging.info(f"{'Would delete' if dry_run else 'Deleted'} subdirectory: {subdirectory}")

    if not found_directories:
        logging.info("No shader cache directories found with files to delete.")

def main():
    """Main entry point for the shader cache cleanup."""
    args = parse_args()
    logging.info("Starting shader cache cleanup...")
    if args.dry_run:
        logging.info("Running in dry-run mode. No files will be deleted.")
    if args.backup:
        logging.info("Backup will be created before deletion.")

    remove_shader_cache(args.dry_run, args.backup)
    logging.info("Shader cache cleanup completed.")

if __name__ == "__main__":
    main()
