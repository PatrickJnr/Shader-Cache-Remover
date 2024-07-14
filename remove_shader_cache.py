import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_files_in_directory(directory: Path):
    """
    Remove all files and directories in the specified directory.

    Args:
        directory (Path): The directory to clear.
    """
    if not directory.exists():
        logging.warning(f"Directory {directory} does not exist.")
        return

    for item in directory.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
                logging.info(f"Deleted file/symlink: {item}")
            elif item.is_dir():
                shutil.rmtree(item)
                logging.info(f"Deleted directory: {item}")
        except FileNotFoundError:
            logging.error(f"File not found: {item}")
        except PermissionError:
            logging.error(f"Permission denied: {item}")
        except Exception as e:
            logging.error(f"Failed to delete {item}. Reason: {e}")

def remove_shader_cache():
    """
    Remove shader cache from known locations on Windows 11.
    """
    shader_cache_directories = [
        Path.home() / 'AppData' / 'Local' / 'NVIDIA' / 'DXCache',
        Path.home() / 'AppData' / 'Local' / 'NVIDIA' / 'GLCache',
        Path.home() / 'AppData' / 'Local' / 'AMD' / 'DxCache',
        Path.home() / 'AppData' / 'Local' / 'UnrealEngine' / 'ShaderCache',
        Path.home() / 'AppData' / 'LocalLow' / 'Unity' / 'Caches',
        Path.home() / 'AppData' / 'Local' / 'D3DSCache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'NVIDIA Corporation' / 'NV_Cache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'DXCache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'D3DSCache',
        Path.home() / 'AppData' / 'Local' / 'Temp' / 'AMD' / 'GLCache',
        Path.home() / 'AppData' / 'Roaming' / 'Unreal Engine' / 'Common' / 'DerivedDataCache',
        Path.home() / 'AppData' / 'Roaming' / 'Unity' / 'Asset Store-5.x',
        Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'CLR_v4.0',
    ]

    for directory in shader_cache_directories:
        logging.info(f"Clearing shader cache in directory: {directory}")
        remove_files_in_directory(directory)

if __name__ == "__main__":
    logging.info("Starting shader cache cleanup...")
    remove_shader_cache()
    logging.info("Shader cache cleanup completed.")
