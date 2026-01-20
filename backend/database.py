"""
Model Scout - SQLite Database (WAL Mode)
Handles caching and historical data storage
"""
import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from config import DATABASE_PATH


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the SQLite database with WAL mode for better concurrency."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    
    cursor = conn.cursor()
    
    # Create benchmark_results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            source TEXT NOT NULL,
            rank INTEGER,
            average_score REAL,
            benchmark_metrics TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(model_name, source, scraped_at)
        )
    """)
    
    # Create comparisons table for caching comparison results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_a TEXT NOT NULL,
            model_b TEXT NOT NULL,
            comparison_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    # Create indexes for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_benchmark_model 
        ON benchmark_results(model_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_benchmark_source 
        ON benchmark_results(source)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_comparison_models 
        ON comparisons(model_a, model_b)
    """)
    
    conn.commit()
    conn.close()


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_benchmark_result(model_name: str, source: str, data: dict):
    """Save a benchmark result to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO benchmark_results 
            (model_name, source, rank, average_score, benchmark_metrics, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            model_name,
            source,
            data.get("rank"),
            data.get("average_score"),
            json.dumps(data.get("benchmark_metrics", {})),
            data.get("scraped_at", datetime.utcnow().isoformat())
        ))
        conn.commit()


def get_cached_result(model_name: str, source: str, max_age_hours: int = 24):
    """Get a cached benchmark result if it exists and is not expired."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        min_time = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
        
        cursor.execute("""
            SELECT * FROM benchmark_results
            WHERE model_name = ? AND source = ? AND scraped_at > ?
            ORDER BY scraped_at DESC
            LIMIT 1
        """, (model_name, source, min_time))
        
        row = cursor.fetchone()
        if row:
            return {
                "model": row["model_name"],
                "source": row["source"],
                "rank": row["rank"],
                "average_score": row["average_score"],
                "benchmark_metrics": json.loads(row["benchmark_metrics"]),
                "scraped_at": row["scraped_at"]
            }
        return None


def save_comparison(model_a: str, model_b: str, data: dict, ttl_hours: int = 24):
    """Save a comparison result with TTL."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()
        
        cursor.execute("""
            INSERT INTO comparisons (model_a, model_b, comparison_data, expires_at)
            VALUES (?, ?, ?, ?)
        """, (model_a, model_b, json.dumps(data), expires_at))
        conn.commit()


def get_model_history(model_name: str, limit: int = 30):
    """Get historical benchmark data for a model."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM benchmark_results
            WHERE model_name = ?
            ORDER BY scraped_at DESC
            LIMIT ?
        """, (model_name, limit))
        
        rows = cursor.fetchall()
        return [{
            "model": row["model_name"],
            "source": row["source"],
            "rank": row["rank"],
            "average_score": row["average_score"],
            "benchmark_metrics": json.loads(row["benchmark_metrics"]),
            "scraped_at": row["scraped_at"]
        } for row in rows]


# Initialize database on module import
init_database()
