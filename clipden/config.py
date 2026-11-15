"""
Configuration management for ClipDen.
Supports .env files, OS environment variables, and secure storage in system Keyring.
"""

import os
from typing import Optional, Tuple
from dotenv import load_dotenv
import keyring

KEYRING_SERVICE = "clipden"
KEYRING_URL_KEY = "supabase_url"
KEYRING_API_KEY = "supabase_key"
KEYRING_SESSION_KEY = "supabase_session"


class Config:
    def __init__(self, env_path: Optional[str] = None):
        if env_path and os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            # Check local .env first, then system environment
            load_dotenv()

        self._url: Optional[str] = None
        self._key: Optional[str] = None
        self._poll_interval: float = 0.35
        self.reload()

    def reload(self) -> None:
        """Reload configuration from environment and keyring."""
        # 1. First priority: Environment variables (or .env)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        # 2. Second priority: System Keyring
        if not url:
            try:
                url = keyring.get_password(KEYRING_SERVICE, KEYRING_URL_KEY)
            except Exception:
                url = None

        if not key:
            try:
                key = keyring.get_password(KEYRING_SERVICE, KEYRING_API_KEY)
            except Exception:
                key = None

        self._url = url.strip() if url else None
        self._key = key.strip() if key else None

        # Poll interval
        try:
            self._poll_interval = float(os.getenv("CLIPBOARD_POLL_INTERVAL", "0.35"))
        except ValueError:
            self._poll_interval = 0.35

    @property
    def supabase_url(self) -> Optional[str]:
        return self._url

    @property
    def supabase_key(self) -> Optional[str]:
        return self._key

    @property
    def poll_interval(self) -> float:
        return self._poll_interval

    @property
    def is_configured(self) -> bool:
        return bool(self._url and self._key)

    def save_credentials(self, url: str, key: str, save_to_keyring: bool = True) -> None:
        """Save credentials to instance, environment, and optionally system keyring."""
        clean_url = url.strip()
        clean_key = key.strip()
        self._url = clean_url
        self._key = clean_key
        os.environ["SUPABASE_URL"] = clean_url
        os.environ["SUPABASE_KEY"] = clean_key

        if save_to_keyring:
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_URL_KEY, clean_url)
                keyring.set_password(KEYRING_SERVICE, KEYRING_API_KEY, clean_key)
            except Exception as e:
                print(f"[Config] Warning: Could not write credentials to keyring: {e}")

    def save_session(self, session_json: str) -> None:
        """Persist user session token in system keyring."""
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_SESSION_KEY, session_json)
        except Exception as e:
            print(f"[Config] Warning: Could not save session to keyring: {e}")

    def get_session(self) -> Optional[str]:
        """Retrieve stored session token from system keyring."""
        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_SESSION_KEY)
        except Exception:
            return None

    def clear_session(self) -> None:
        """Remove stored session token from system keyring."""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_SESSION_KEY)
        except Exception:
            pass


# Singleton instance
config = Config()
