"""
Filesystem abstraction for the Shader Cache Remover.

This module provides both real and mock filesystem implementations,
enabling thorough testing without actual file system modifications.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set
from dataclasses import dataclass, field
import stat


class RealFileSystem:
    """
    Real filesystem implementation.
    
    Delegates all operations to the actual operating system.
    """
    
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        return path.exists()
    
    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        return path.is_file()
    
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        return path.is_dir()
    
    def iterdir(self, path: Path) -> List[Path]:
        """List directory contents."""
        return list(path.iterdir())
    
    def rglob(self, path: Path, pattern: str) -> List[Path]:
        """Recursively glob for files matching pattern."""
        return list(path.rglob(pattern))
    
    def stat_size(self, path: Path) -> int:
        """Get file size in bytes."""
        return path.stat().st_size
    
    def unlink(self, path: Path) -> None:
        """Delete a file."""
        path.unlink()
    
    def rmtree(self, path: Path) -> None:
        """Recursively delete a directory."""
        shutil.rmtree(path)
    
    def copytree(self, src: Path, dst: Path, dirs_exist_ok: bool = False) -> None:
        """Copy a directory tree."""
        shutil.copytree(src, dst, dirs_exist_ok=dirs_exist_ok)
    
    def copy2(self, src: Path, dst: Path) -> None:
        """Copy a file preserving metadata."""
        shutil.copy2(src, dst)
    
    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        path.mkdir(parents=parents, exist_ok=exist_ok)


@dataclass
class MockFile:
    """Represents a file in the mock filesystem."""
    content: bytes = b""
    size: int = 0
    mode: int = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH


class MockFileSystem:
    """
    In-memory filesystem for testing.
    
    Provides a complete mock of filesystem operations without
    touching the real filesystem. Useful for unit tests.
    
    Usage:
        fs = MockFileSystem()
        fs.add_file(Path("/test/file.txt"), b"content")
        fs.add_directory(Path("/test/cache"))
        
        # Use with services
        cleanup_service = CleanupService(filesystem=fs)
        
        # Check what was deleted
        assert Path("/test/file.txt") in fs.get_deleted()
    """
    
    def __init__(self):
        """Initialize empty mock filesystem."""
        self._files: Dict[Path, MockFile] = {}
        self._directories: Set[Path] = set()
        self._deleted_files: List[Path] = []
        self._deleted_dirs: List[Path] = []
    
    def add_file(self, path: Path, content: bytes = b"", size: Optional[int] = None) -> None:
        """
        Add a file to the mock filesystem.
        
        Args:
            path: Path to the file
            content: File content (optional)
            size: File size (if different from content length)
        """
        path = path.resolve()
        self._files[path] = MockFile(
            content=content,
            size=size if size is not None else len(content)
        )
        # Ensure parent directories exist
        for parent in path.parents:
            self._directories.add(parent)
    
    def add_directory(self, path: Path) -> None:
        """
        Add a directory to the mock filesystem.
        
        Args:
            path: Path to the directory
        """
        path = path.resolve()
        self._directories.add(path)
        for parent in path.parents:
            self._directories.add(parent)
    
    def exists(self, path: Path) -> bool:
        """Check if path exists."""
        path = path.resolve()
        return path in self._files or path in self._directories
    
    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        return path.resolve() in self._files
    
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        return path.resolve() in self._directories
    
    def iterdir(self, path: Path) -> List[Path]:
        """List directory contents."""
        path = path.resolve()
        if path not in self._directories:
            raise FileNotFoundError(f"Directory not found: {path}")
        
        children = []
        
        # Find immediate child files
        for file_path in self._files:
            if file_path.parent == path:
                children.append(file_path)
        
        # Find immediate child directories
        for dir_path in self._directories:
            if dir_path.parent == path and dir_path != path:
                children.append(dir_path)
        
        return children
    
    def rglob(self, path: Path, pattern: str) -> List[Path]:
        """Recursively find files matching pattern."""
        path = path.resolve()
        matches = []
        
        for file_path in self._files:
            if str(file_path).startswith(str(path)):
                if pattern == "*" or file_path.match(pattern):
                    matches.append(file_path)
        
        return matches
    
    def stat_size(self, path: Path) -> int:
        """Get file size in bytes."""
        path = path.resolve()
        if path in self._files:
            return self._files[path].size
        raise FileNotFoundError(f"File not found: {path}")
    
    def unlink(self, path: Path) -> None:
        """Delete a file."""
        path = path.resolve()
        if path not in self._files:
            raise FileNotFoundError(f"File not found: {path}")
        del self._files[path]
        self._deleted_files.append(path)
    
    def rmtree(self, path: Path) -> None:
        """Recursively delete a directory."""
        path = path.resolve()
        if path not in self._directories:
            raise FileNotFoundError(f"Directory not found: {path}")
        
        # Delete all files under this directory
        files_to_delete = [f for f in self._files if str(f).startswith(str(path))]
        for file_path in files_to_delete:
            del self._files[file_path]
            self._deleted_files.append(file_path)
        
        # Delete all subdirectories
        dirs_to_delete = [d for d in self._directories 
                        if str(d).startswith(str(path)) and d != path]
        for dir_path in sorted(dirs_to_delete, reverse=True):
            self._directories.discard(dir_path)
            self._deleted_dirs.append(dir_path)
        
        # Delete the directory itself
        self._directories.discard(path)
        self._deleted_dirs.append(path)
    
    def copytree(self, src: Path, dst: Path, dirs_exist_ok: bool = False) -> None:
        """Copy a directory tree."""
        src = src.resolve()
        dst = dst.resolve()
        
        if not dirs_exist_ok and dst in self._directories:
            raise FileExistsError(f"Directory exists: {dst}")
        
        # Copy directory structure
        self._directories.add(dst)
        for dir_path in self._directories:
            if str(dir_path).startswith(str(src)):
                relative = dir_path.relative_to(src)
                self._directories.add(dst / relative)
        
        # Copy files
        for file_path, mock_file in list(self._files.items()):
            if str(file_path).startswith(str(src)):
                relative = file_path.relative_to(src)
                new_path = dst / relative
                self._files[new_path] = MockFile(
                    content=mock_file.content,
                    size=mock_file.size
                )
    
    def copy2(self, src: Path, dst: Path) -> None:
        """Copy a file preserving metadata."""
        src = src.resolve()
        dst = dst.resolve()
        
        if src not in self._files:
            raise FileNotFoundError(f"Source file not found: {src}")
        
        self._files[dst] = MockFile(
            content=self._files[src].content,
            size=self._files[src].size
        )
    
    def mkdir(self, path: Path, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        path = path.resolve()
        
        if path in self._directories:
            if exist_ok:
                return
            raise FileExistsError(f"Directory exists: {path}")
        
        if parents:
            for parent in reversed(path.parents):
                self._directories.add(parent)
        
        self._directories.add(path)
    
    # Test helper methods
    
    def get_deleted_files(self) -> List[Path]:
        """Get list of deleted files for test assertions."""
        return self._deleted_files.copy()
    
    def get_deleted_dirs(self) -> List[Path]:
        """Get list of deleted directories for test assertions."""
        return self._deleted_dirs.copy()
    
    def get_all_deleted(self) -> List[Path]:
        """Get all deleted paths (files and directories)."""
        return self._deleted_files + self._deleted_dirs
    
    def reset_deletion_tracking(self) -> None:
        """Clear deletion tracking lists."""
        self._deleted_files.clear()
        self._deleted_dirs.clear()
