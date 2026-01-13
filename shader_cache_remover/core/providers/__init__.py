"""
Cache provider implementations for the Shader Cache Remover.

This package contains built-in cache detection providers.
"""

from .base import BaseCacheProvider
from .steam import SteamProvider
from .nvidia import NVIDIAProvider
from .amd import AMDProvider
from .intel import IntelProvider
from .unreal import UnrealEngineProvider
from .unity import UnityProvider
from .system import SystemCacheProvider
from .custom import CustomPathProvider
from .epic import EpicGamesProvider
from .gog import GOGProvider
from .ea import EAProvider
from .browser import BrowserCacheProvider

__all__ = [
    "BaseCacheProvider",
    "SteamProvider",
    "NVIDIAProvider",
    "AMDProvider",
    "IntelProvider",
    "UnrealEngineProvider",
    "UnityProvider",
    "SystemCacheProvider",
    "CustomPathProvider",
    "EpicGamesProvider",
    "GOGProvider",
    "EAProvider",
    "BrowserCacheProvider",
]

