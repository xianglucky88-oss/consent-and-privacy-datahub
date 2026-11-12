import sqlite3

from consent_privacy.pipeline import run_pipeline


def test_latest_event_materializes_revocation(tmp_path):
    db = tmp_path / "privacy.sqlite3"
    result = run_pipeline([
        {"event_id": "1", "subject_id": "s", "policy_version": "v1", "purpose": "analytics", "scope": "orders", "action": "grant", "occurred_at": "2026-01-01T00:00:00Z", "source": "web"},
        {"event_id": "2", "subject_id": "s", "policy_version": "v1", "purpose": "analytics", "scope": "orders", "action": "revoke", "occurred_at": "2026-01-02T00:00:00Z", "source": "portal"},
    ], db)
    assert result["current_records"] == 1
    with sqlite3.connect(db) as conn:
        assert conn.execute("select status from current_consent").fetchone()[0] == "revoked"
