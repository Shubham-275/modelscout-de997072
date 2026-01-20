"""
Model Scout - Phase 2: Database Schema Extension

PHASE 2 REQUIREMENTS:
- Snapshot storage with integrity hashes
- Extraction history for temporal tracking
- Regression event logging
- Full audit trail
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any


def init_phase2_schema(conn: sqlite3.Connection) -> None:
    """
    Initialize Phase 2 database tables.
    
    Tables:
    - snapshots: Immutable snapshot storage with hashes
    - extraction_history: Temporal extraction tracking
    - regression_events: Logged regression detections
    - prs_history: PRS computation history
    """
    cursor = conn.cursor()
    
    # Snapshots table - immutable, with content hash
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id TEXT PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            model_ids TEXT NOT NULL,  -- JSON array
            model_scores TEXT NOT NULL,  -- JSON object
            benchmark_versions TEXT NOT NULL,  -- JSON array
            weights_used TEXT,  -- JSON object
            extraction_source TEXT DEFAULT 'mino',
            phase TEXT DEFAULT 'phase-2',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            -- Integrity enforcement
            UNIQUE(content_hash)
        )
    """)
    
    # Index for snapshot queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
        ON snapshots(timestamp_utc DESC)
    """)
    
    # Extraction history table - for temporal tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extraction_history (
            extraction_id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            benchmark_id TEXT NOT NULL,
            benchmark_version TEXT NOT NULL,
            status TEXT NOT NULL,  -- 'success' | 'failure' | 'partial'
            scores TEXT,  -- JSON object of metric -> score
            timestamp_utc TEXT NOT NULL,
            source_url TEXT,
            error_code TEXT,
            error_message TEXT,
            snapshot_id TEXT,  -- Reference to containing snapshot
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    """)
    
    # Composite index for efficient temporal queries (same model+benchmark+version)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_extraction_temporal
        ON extraction_history(model_id, benchmark_id, benchmark_version, timestamp_utc DESC)
    """)
    
    # Regression events table - audit trail
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regression_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            benchmark_id TEXT NOT NULL,
            benchmark_category TEXT NOT NULL,
            current_score REAL NOT NULL,
            previous_score REAL NOT NULL,
            delta_absolute REAL NOT NULL,
            delta_percentage REAL NOT NULL,
            severity TEXT NOT NULL,  -- 'none' | 'minor' | 'major'
            thresholds_used TEXT,  -- JSON object
            current_snapshot_id TEXT NOT NULL,
            previous_snapshot_id TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (current_snapshot_id) REFERENCES snapshots(snapshot_id),
            FOREIGN KEY (previous_snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    """)
    
    # Index for regression queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_regression_model
        ON regression_events(model_id, detected_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_regression_severity
        ON regression_events(severity, detected_at DESC)
    """)
    
    # PRS history table - for tracking PRS over time
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prs_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            snapshot_id TEXT NOT NULL,
            final_prs REAL NOT NULL,
            capability_consistency REAL NOT NULL,
            benchmark_stability REAL NOT NULL,
            temporal_reliability REAL NOT NULL,
            benchmarks_included TEXT,  -- JSON array
            missing_benchmarks TEXT,  -- JSON array
            extraction_count INTEGER,
            computation_timestamp TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id)
        )
    """)
    
    # Index for PRS queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prs_model
        ON prs_history(model_id, computation_timestamp DESC)
    """)
    
    conn.commit()


def save_snapshot(conn: sqlite3.Connection, snapshot_data: Dict[str, Any]) -> str:
    """
    Save a snapshot to the database.
    
    Enforces immutability - duplicate hashes are rejected.
    
    Returns:
        snapshot_id of saved snapshot
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO snapshots (
                snapshot_id, timestamp_utc, content_hash,
                model_ids, model_scores, benchmark_versions,
                weights_used, extraction_source, phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_data["snapshot_id"],
            snapshot_data["timestamp_utc"],
            snapshot_data["content_hash"],
            json.dumps(snapshot_data["model_ids"]),
            json.dumps(snapshot_data["model_scores"]),
            json.dumps(snapshot_data.get("benchmark_versions", [])),
            json.dumps(snapshot_data.get("weights_used", {})),
            snapshot_data.get("extraction_source", "mino"),
            snapshot_data.get("phase", "phase-2")
        ))
        conn.commit()
        return snapshot_data["snapshot_id"]
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: snapshots.content_hash" in str(e):
            raise ValueError("Snapshot with identical content already exists (immutability enforced)")
        raise


def get_snapshot(conn: sqlite3.Connection, snapshot_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a snapshot by ID."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT snapshot_id, timestamp_utc, content_hash,
               model_ids, model_scores, benchmark_versions,
               weights_used, extraction_source, phase
        FROM snapshots
        WHERE snapshot_id = ?
    """, (snapshot_id,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        "snapshot_id": row[0],
        "timestamp_utc": row[1],
        "content_hash": row[2],
        "model_ids": json.loads(row[3]),
        "model_scores": json.loads(row[4]),
        "benchmark_versions": json.loads(row[5]),
        "weights_used": json.loads(row[6]) if row[6] else {},
        "extraction_source": row[7],
        "phase": row[8]
    }


def get_latest_snapshots(conn: sqlite3.Connection, limit: int = 2) -> List[Dict[str, Any]]:
    """Get the N most recent snapshots."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT snapshot_id, timestamp_utc, content_hash,
               model_ids, model_scores, benchmark_versions,
               weights_used, extraction_source, phase
        FROM snapshots
        ORDER BY timestamp_utc DESC
        LIMIT ?
    """, (limit,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "snapshot_id": row[0],
            "timestamp_utc": row[1],
            "content_hash": row[2],
            "model_ids": json.loads(row[3]),
            "model_scores": json.loads(row[4]),
            "benchmark_versions": json.loads(row[5]),
            "weights_used": json.loads(row[6]) if row[6] else {},
            "extraction_source": row[7],
            "phase": row[8]
        })
    
    return results


def save_extraction_record(conn: sqlite3.Connection, record: Dict[str, Any]) -> str:
    """Save an extraction record."""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO extraction_history (
            extraction_id, model_id, benchmark_id, benchmark_version,
            status, scores, timestamp_utc, source_url,
            error_code, error_message, snapshot_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["extraction_id"],
        record["model_id"],
        record["benchmark_id"],
        record["benchmark_version"],
        record["status"],
        json.dumps(record.get("scores", {})),
        record["timestamp_utc"],
        record.get("source_url"),
        record.get("error_code"),
        record.get("error_message"),
        record.get("snapshot_id")
    ))
    
    conn.commit()
    return record["extraction_id"]


def get_extraction_history(
    conn: sqlite3.Connection,
    model_id: str,
    benchmark_id: str,
    version: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get extraction history for temporal analysis."""
    cursor = conn.cursor()
    
    if version:
        cursor.execute("""
            SELECT extraction_id, model_id, benchmark_id, benchmark_version,
                   status, scores, timestamp_utc, source_url,
                   error_code, error_message, snapshot_id
            FROM extraction_history
            WHERE model_id = ? AND benchmark_id = ? AND benchmark_version = ?
            ORDER BY timestamp_utc DESC
            LIMIT ?
        """, (model_id, benchmark_id, version, limit))
    else:
        cursor.execute("""
            SELECT extraction_id, model_id, benchmark_id, benchmark_version,
                   status, scores, timestamp_utc, source_url,
                   error_code, error_message, snapshot_id
            FROM extraction_history
            WHERE model_id = ? AND benchmark_id = ?
            ORDER BY timestamp_utc DESC
            LIMIT ?
        """, (model_id, benchmark_id, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "extraction_id": row[0],
            "model_id": row[1],
            "benchmark_id": row[2],
            "benchmark_version": row[3],
            "status": row[4],
            "scores": json.loads(row[5]) if row[5] else {},
            "timestamp_utc": row[6],
            "source_url": row[7],
            "error_code": row[8],
            "error_message": row[9],
            "snapshot_id": row[10]
        })
    
    return results


def save_regression_event(conn: sqlite3.Connection, event: Dict[str, Any]) -> int:
    """Save a regression event to the audit trail."""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO regression_events (
            model_id, benchmark_id, benchmark_category,
            current_score, previous_score, delta_absolute, delta_percentage,
            severity, thresholds_used,
            current_snapshot_id, previous_snapshot_id, detected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event["model_id"],
        event["benchmark_id"],
        event["benchmark_category"],
        event["current_score"],
        event["previous_score"],
        event["delta_absolute"],
        event["delta_percentage"],
        event["severity"],
        json.dumps(event.get("thresholds_used", {})),
        event["current_snapshot_id"],
        event["previous_snapshot_id"],
        event["detected_at"]
    ))
    
    conn.commit()
    return cursor.lastrowid


def get_regression_history(
    conn: sqlite3.Connection,
    model_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get regression history with optional filters."""
    cursor = conn.cursor()
    
    query = "SELECT * FROM regression_events WHERE 1=1"
    params = []
    
    if model_id:
        query += " AND model_id = ?"
        params.append(model_id)
    
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    
    query += " ORDER BY detected_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    columns = [description[0] for description in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        result = dict(zip(columns, row))
        if result.get("thresholds_used"):
            result["thresholds_used"] = json.loads(result["thresholds_used"])
        results.append(result)
    
    return results


def save_prs_record(conn: sqlite3.Connection, record: Dict[str, Any]) -> int:
    """Save a PRS computation record."""
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO prs_history (
            model_id, snapshot_id, final_prs,
            capability_consistency, benchmark_stability, temporal_reliability,
            benchmarks_included, missing_benchmarks, extraction_count,
            computation_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["model_id"],
        record["snapshot_id"],
        record["final_prs"],
        record["capability_consistency"],
        record["benchmark_stability"],
        record["temporal_reliability"],
        json.dumps(record.get("benchmarks_included", [])),
        json.dumps(record.get("missing_benchmarks", [])),
        record.get("extraction_count", 0),
        record["computation_timestamp"]
    ))
    
    conn.commit()
    return cursor.lastrowid


def get_prs_history(
    conn: sqlite3.Connection,
    model_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get PRS history for a model."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT model_id, snapshot_id, final_prs,
               capability_consistency, benchmark_stability, temporal_reliability,
               benchmarks_included, missing_benchmarks, extraction_count,
               computation_timestamp
        FROM prs_history
        WHERE model_id = ?
        ORDER BY computation_timestamp DESC
        LIMIT ?
    """, (model_id, limit))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "model_id": row[0],
            "snapshot_id": row[1],
            "final_prs": row[2],
            "capability_consistency": row[3],
            "benchmark_stability": row[4],
            "temporal_reliability": row[5],
            "benchmarks_included": json.loads(row[6]) if row[6] else [],
            "missing_benchmarks": json.loads(row[7]) if row[7] else [],
            "extraction_count": row[8],
            "computation_timestamp": row[9]
        })
    
    return results
