import os
import shutil

def remove_files_in_directory(directory):
    """Remove all files and directories in the specified directory."""
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"Directory {directory} does not exist.")

def remove_shader_cache():
    """Remove shader cache from known locations on Windows 11."""
    # Known shader cache locations for Windows 11
    shader_cache_directories = [
        os.path.expanduser('~\\AppData\\Local\\NVIDIA\\DXCache'),  # NVIDIA DXCache
        os.path.expanduser('~\\AppData\\Local\\NVIDIA\\GLCache'),  # NVIDIA GLCache
        os.path.expanduser('~\\AppData\\Local\\AMD\\DxCache'),     # AMD DXCache
        os.path.expanduser('~\\AppData\\Local\\UnrealEngine\\ShaderCache'),  # Unreal Engine
        os.path.expanduser('~\\AppData\\LocalLow\\Unity\\Caches'),  # Unity
        os.path.expanduser('~\\AppData\\Local\\D3DSCache'),  # DirectX Shader Cache
        os.path.expanduser('~\\AppData\\Local\\Temp\\NVIDIA Corporation\\NV_Cache'),  # NVIDIA Temp Cache
        os.path.expanduser('~\\AppData\\Local\\Temp\\DXCache'),  # DirectX Temp Cache
        os.path.expanduser('~\\AppData\\Local\\Temp\\D3DSCache'),  # DirectX Shader Temp Cache
        os.path.expanduser('~\\AppData\\Local\\Temp\\AMD\\GLCache'),  # AMD Temp GL Cache
        os.path.expanduser('~\\AppData\\Roaming\\Unreal Engine\\Common\\DerivedDataCache'),  # Unreal Engine Derived Data Cache
        os.path.expanduser('~\\AppData\\Roaming\\Unity\\Asset Store-5.x'),  # Unity Asset Store Cache
        os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\CLR_v4.0'),  # .NET CLR cache (sometimes used for shader caches)
    ]

    for directory in shader_cache_directories:
        remove_files_in_directory(directory)

if __name__ == "__main__":
    remove_shader_cache()
