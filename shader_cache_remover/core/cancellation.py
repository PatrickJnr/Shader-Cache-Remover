"""
Cancellation token for cooperative cancellation of long-running operations.

This module provides a thread-safe mechanism for signaling cancellation
to long-running operations like cleanup and backup.
"""

import threading
from typing import Callable, List, Optional


class CancelledException(Exception):
    """
    Exception raised when an operation is cancelled.
    
    This exception should be caught at operation boundaries to
    gracefully handle cancellation.
    """
    pass


class CancellationToken:
    """
    Token for cooperative cancellation of long-running operations.
    
    Usage:
        token = CancellationToken()
        
        # In worker thread:
        for item in items:
            token.throw_if_cancelled()
            process(item)
        
        # To cancel from another thread:
        token.cancel()
    """
    
    def __init__(self):
        """Initialize a new cancellation token."""
        self._cancelled = threading.Event()
        self._callbacks: List[Callable[[], None]] = []
        self._lock = threading.Lock()
    
    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled.is_set()
    
    def cancel(self) -> None:
        """
        Request cancellation.
        
        This method is thread-safe and can be called from any thread.
        All registered callbacks will be invoked.
        """
        self._cancelled.set()
        
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback()
            except Exception:
                pass  # Don't let callback errors prevent other callbacks
    
    def throw_if_cancelled(self) -> None:
        """
        Raise CancelledException if cancellation has been requested.
        
        This should be called at safe points during long-running operations
        to allow cooperative cancellation.
        
        Raises:
            CancelledException: If cancellation was requested.
        """
        if self.is_cancelled:
            raise CancelledException("Operation was cancelled")
    
    def on_cancel(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to be invoked when cancellation is requested.
        
        If cancellation has already been requested, the callback is
        invoked immediately.
        
        Args:
            callback: Function to call on cancellation.
        """
        with self._lock:
            self._callbacks.append(callback)
        
        if self.is_cancelled:
            try:
                callback()
            except Exception:
                pass
    
    def reset(self) -> None:
        """
        Reset the token for reuse.
        
        Warning: Only call this if you're certain no operations are
        currently checking this token.
        """
        self._cancelled.clear()
        with self._lock:
            self._callbacks.clear()


class CancellationTokenSource:
    """
    Factory for creating linked cancellation tokens.
    
    Useful for creating child tokens that are cancelled when the parent
    is cancelled, but can also be cancelled independently.
    """
    
    def __init__(self, parent: Optional[CancellationToken] = None):
        """
        Create a new token source.
        
        Args:
            parent: Optional parent token. If provided, cancelling the
                   parent will also cancel tokens from this source.
        """
        self._token = CancellationToken()
        
        if parent is not None:
            parent.on_cancel(self._token.cancel)
    
    @property
    def token(self) -> CancellationToken:
        """Get the cancellation token."""
        return self._token
    
    def cancel(self) -> None:
        """Cancel the token."""
        self._token.cancel()
