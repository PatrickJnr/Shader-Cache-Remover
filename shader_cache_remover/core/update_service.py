import json
import logging
import urllib.request
import urllib.error
import webbrowser
from typing import Optional, Tuple, Dict, Any
from packaging import version

from shader_cache_remover import __version__

logger = logging.getLogger(__name__)

class UpdateService:
    """
    Service to check for application updates via GitHub API.
    """
    
    GITHUB_REPO = "PatrickJnr/Shader-Cache-Remover"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    @staticmethod
    def get_current_version() -> str:
        """Returns the current installed version."""
        return __version__
    
    @classmethod
    def check_for_updates(cls) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Checks if a newer version is available.
        
        Returns:
            Tuple containing:
            - update_available (bool): True if update exists
            - latest_version (str): The version string of the latest release (e.g. "1.7.0")
            - download_url (str): URL to the release page or asset
            - release_notes (str): Body text of the release
        """
        try:
            logger.info(f"Checking for updates. Current version: {__version__}")
            
            # Create request with User-Agent to satisfy GitHub API requirement
            req = urllib.request.Request(
                cls.API_URL, 
                headers={'User-Agent': 'Shader-Cache-Remover-App'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    logger.warning(f"GitHub API returned status {response.status}")
                    return False, None, None, None
                
                data: Dict[str, Any] = json.loads(response.read().decode('utf-8'))
                
                latest_tag = data.get('tag_name', '').lstrip('v')
                html_url = data.get('html_url')
                body = data.get('body', 'No release notes available.')
                
                if not latest_tag:
                    logger.warning("Could not parse tag_name from GitHub response")
                    return False, None, None, None
                
                # Compare versions using packaging.version
                current_v = version.parse(__version__)
                latest_v = version.parse(latest_tag)
                
                if latest_v > current_v:
                    logger.info(f"Update available: {latest_tag} (Current: {__version__})")
                    return True, latest_tag, html_url, body
                else:
                    logger.info("Application is up to date.")
                    return False, latest_tag, html_url, body
                    
        except urllib.error.URLError as e:
            logger.error(f"Network error checking for updates: {e}")
            return False, None, None, None
        except Exception as e:
            logger.error(f"Unexpected error checking for updates: {e}", exc_info=True)
            return False, None, None, None

    @staticmethod
    def open_download_page(url: str) -> None:
        """Opens the download URL in the default browser."""
        if url:
            webbrowser.open(url)
