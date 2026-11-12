from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

VALID_ACTIONS = {"grant", "revoke", "erase", "export"}


def normalize(row: dict) -> dict:
    occurred_at = datetime.fromisoformat(str(row["occurred_at"]).replace("Z", "+00:00")).isoformat()
    event = {
        "event_id": str(row["event_id"]),
        "subject_id": str(row["subject_id"]).strip(),
        "policy_version": str(row["policy_version"]).strip(),
        "purpose": str(row["purpose"]).strip().lower(),
        "scope": str(row["scope"]).strip().lower(),
        "action": str(row["action"]).strip().lower(),
        "occurred_at": occurred_at,
        "source": str(row["source"]).strip().lower(),
    }
    if not event["subject_id"] or event["action"] not in VALID_ACTIONS:
        raise ValueError("subject_id and supported action are required")
    return event


def _schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS consent_events (
            event_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL, policy_version TEXT NOT NULL,
            purpose TEXT NOT NULL, scope TEXT NOT NULL, action TEXT NOT NULL,
            occurred_at TEXT NOT NULL, source TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS current_consent (
            subject_id TEXT NOT NULL, purpose TEXT NOT NULL, scope TEXT NOT NULL,
            status TEXT NOT NULL, policy_version TEXT NOT NULL, changed_at TEXT NOT NULL,
            source TEXT NOT NULL, PRIMARY KEY(subject_id, purpose, scope)
        );
        CREATE TABLE IF NOT EXISTS rejected_events (
            event_id TEXT, reason TEXT NOT NULL, raw_json TEXT NOT NULL
        );
        """
    )


def run_pipeline(records: Iterable[dict], database: str | Path) -> dict[str, int]:
    conn = sqlite3.connect(database)
    _schema(conn)
    accepted = rejected = duplicates = 0
    for raw in records:
        try:
            event = normalize(raw)
            cur = conn.execute("INSERT OR IGNORE INTO consent_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)", tuple(event.values()))
            if cur.rowcount:
                accepted += 1
            else:
                duplicates += 1
        except (KeyError, TypeError, ValueError) as exc:
            rejected += 1
            conn.execute("INSERT INTO rejected_events VALUES (?, ?, ?)", (str(raw.get("event_id")), str(exc), json.dumps(raw, sort_keys=True)))
    latest: dict[tuple[str, str, str], tuple] = {}
    for row in conn.execute("SELECT subject_id, purpose, scope, action, policy_version, occurred_at, source FROM consent_events ORDER BY occurred_at, event_id"):
        latest[(row[0], row[1], row[2])] = row
    for row in latest.values():
        status = {"grant": "active", "revoke": "revoked", "erase": "erasure_requested", "export": "export_requested"}[row[3]]
        conn.execute("INSERT OR REPLACE INTO current_consent VALUES (?, ?, ?, ?, ?, ?, ?)", (row[0], row[1], row[2], status, row[4], row[5], row[6]))
    conn.commit()
    result = {"accepted": accepted, "rejected": rejected, "duplicates": duplicates, "current_records": len(latest)}
    conn.close()
    return result
