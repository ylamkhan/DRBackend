# app/security/token_blacklist.py
from typing import Set
from datetime import datetime, timedelta
import threading

class TokenBlacklistManager:
    def __init__(self):
        self._blacklisted_tokens: Set[str] = set()
        self._lock = threading.Lock()
    
    def add_token(self, token: str) -> None:
        """Add a token to the blacklist"""
        with self._lock:
            self._blacklisted_tokens.add(token)
            print(f"Token added to blacklist. Total: {len(self._blacklisted_tokens)}")
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        with self._lock:
            return token in self._blacklisted_tokens
    
    def remove_token(self, token: str) -> None:
        """Remove a token from the blacklist (useful for cleanup)"""
        with self._lock:
            self._blacklisted_tokens.discard(token)
    
    def get_blacklist_size(self) -> int:
        """Get the current size of the blacklist"""
        with self._lock:
            return len(self._blacklisted_tokens)
    
    def clear_blacklist(self) -> None:
        """Clear all tokens from the blacklist"""
        with self._lock:
            self._blacklisted_tokens.clear()

# Create a singleton instance
blacklist_manager = TokenBlacklistManager()