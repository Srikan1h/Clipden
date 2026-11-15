"""
Integration and unit tests for Supabase database operations in ClipDen.
"""

import pytest
from clipden.database import db_service


def test_database_connection():
    connected, msg = db_service.test_connection()
    assert connected is True, f"Database connection failed: {msg}"


def test_database_crud_lifecycle():
    # 1. Create
    snippet = db_service.create_snippet(
        title="Integration Test Snippet",
        content="Testing CRUD operations against Supabase PostgreSQL",
        source="manual",
    )
    assert snippet is not None
    snippet_id = snippet["id"]
    assert snippet["title"] == "Integration Test Snippet"
    assert snippet["source"] == "manual"

    try:
        # 2. Read / Search
        results = db_service.get_snippets(search_query="Integration Test Snippet")
        assert any(s["id"] == snippet_id for s in results)

        # 3. Update
        updated = db_service.update_snippet(
            snippet_id=snippet_id,
            title="Updated Title",
            content="Updated Content",
        )
        assert updated["title"] == "Updated Title"
        assert updated["content"] == "Updated Content"
        assert updated["updated_at"] >= snippet["created_at"]

    finally:
        # 4. Delete
        deleted = db_service.delete_snippet(snippet_id)
        assert deleted is True

        # Verify deletion
        verify = db_service.get_snippets(search_query="Updated Title")
        assert not any(s["id"] == snippet_id for s in verify)


def test_validation_errors():
    with pytest.raises(ValueError):
        db_service.create_snippet(title="", content="some content")

    with pytest.raises(ValueError):
        db_service.create_snippet(title="Valid title", content="   ")

