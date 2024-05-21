import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_files_in_directory(directory: Path):
    """
    Remove all files and directories in the specified directory.

    Args:
        directory (Path): The directory to clear.
    """
    if directory.exists():
        for item in directory.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                logging.info(f"Deleted: {item}")
            except Exception as e:
                logging.error(f"Failed to delete {item}. Reason: {e}")
    else:
        logging.warning(f"Directory {directory} does not exist.")

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
        remove_files_in_directory(directory)

if __name__ == "__main__":
    remove_shader_cache()
