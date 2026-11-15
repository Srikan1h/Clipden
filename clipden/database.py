"""
Database service wrapping Supabase client operations for ClipDen.
Provides thread-safe CRUD operations, search, and session management.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Tuple
from supabase import Client, create_client

from clipden.config import config
from clipden.utils import validate_snippet


class DatabaseService:
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self._url = url or config.supabase_url
        self._key = key or config.supabase_key
        self._client: Optional[Client] = None
        self._user_id: Optional[str] = None
        self._init_client()

    def _init_client(self) -> None:
        if not self._url or not self._key:
            return

        try:
            self._client = create_client(self._url, self._key)
            self._setup_auth()
        except Exception as e:
            print(f"[DatabaseService] Init client failed: {e}")
            self._client = None

    def _setup_auth(self) -> None:
        """Attempt to restore or establish session, including anonymous sign-in."""
        if not self._client:
            return

        # 1. Try to restore saved session from keyring
        saved_session = config.get_session()
        if saved_session:
            try:
                data = json.loads(saved_session)
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                if access_token and refresh_token:
                    res = self._client.auth.set_session(access_token, refresh_token)
                    if res.user:
                        self._user_id = res.user.id
                        return
            except Exception as e:
                print(f"[DatabaseService] Restoring saved session failed: {e}")
                config.clear_session()

        # 2. Try anonymous sign-in
        try:
            res = self._client.auth.sign_in_anonymously()
            if res.user and res.session:
                self._user_id = res.user.id
                session_data = {
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "user_id": res.user.id,
                }
                config.save_session(json.dumps(session_data))
                print(f"[DatabaseService] Anonymous session established for user {self._user_id}")
        except Exception as e:
            # If anonymous sign-ins are disabled on Supabase, anon key operations will still work with RLS
            print(f"[DatabaseService] Anonymous sign-in not available ({e}), proceeding with anon key.")

    def reload_credentials(self, url: str, key: str) -> Tuple[bool, str]:
        """Update client with new credentials and test connectivity."""
        self._url = url.strip()
        self._key = key.strip()
        try:
            self._client = create_client(self._url, self._key)
            self._setup_auth()
            return self.test_connection()
        except Exception as e:
            return False, str(e)

    def test_connection(self) -> Tuple[bool, str]:
        """Test database connection by checking snippets table."""
        if not self._client:
            return False, "Supabase client is not configured. Check URL and Key."

        try:
            res = self._client.table("snippets").select("id").limit(1).execute()
            return True, "Connected successfully to Supabase."
        except Exception as e:
            return False, f"Connection error: {e}"

    def create_snippet(self, title: str, content: str, source: str = "manual") -> Dict[str, Any]:
        """
        Create a new snippet in Supabase.
        Validates title and content before insertion.
        Source must be 'manual' or 'clipboard'.
        """
        if not self._client:
            raise ConnectionError("Database client not configured.")

        is_valid, err_msg = validate_snippet(title, content)
        if not is_valid:
            raise ValueError(err_msg)

        if source not in ("manual", "clipboard"):
            source = "manual"

        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "title": title.strip(),
            "content": content,
            "source": source,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        if self._user_id:
            payload["user_id"] = self._user_id

        res = self._client.table("snippets").insert(payload).execute()
        if not res.data:
            raise RuntimeError("Insert succeeded but no record was returned.")
        return res.data[0]

    def get_snippets(
        self,
        search_query: Optional[str] = None,
        source_filter: Optional[str] = None,
        limit: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve snippets ordered by newest first.
        Supports search across title and content, and filtering by source.
        """
        if not self._client:
            return []

        try:
            query = self._client.table("snippets").select("*")

            if source_filter and source_filter in ("manual", "clipboard"):
                query = query.eq("source", source_filter)

            if search_query and search_query.strip():
                term = f"%{search_query.strip()}%"
                # PostgREST or filter: title.ilike.term,content.ilike.term
                query = query.or_(f"title.ilike.{term},content.ilike.{term}")

            res = query.order("created_at", desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            print(f"[DatabaseService] get_snippets error: {e}")
            raise e

    def update_snippet(self, snippet_id: str, title: str, content: str) -> Dict[str, Any]:
        """
        Update an existing snippet's title and content.
        Sets updated_at timestamp to now.
        """
        if not self._client:
            raise ConnectionError("Database client not configured.")

        is_valid, err_msg = validate_snippet(title, content)
        if not is_valid:
            raise ValueError(err_msg)

        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "title": title.strip(),
            "content": content,
            "updated_at": now_iso,
        }

        res = self._client.table("snippets").update(payload).eq("id", snippet_id).execute()
        if not res.data:
            raise RuntimeError(f"Snippet with ID {snippet_id} not found or update failed.")
        return res.data[0]

    def delete_snippet(self, snippet_id: str) -> bool:
        """
        Delete a snippet by ID.
        """
        if not self._client:
            raise ConnectionError("Database client not configured.")

        res = self._client.table("snippets").delete().eq("id", snippet_id).execute()
        return bool(res.data)


# Global database service instance
db_service = DatabaseService()

