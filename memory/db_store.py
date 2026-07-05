import sqlite3
from pathlib import Path

# Resolve database file path relative to the project root
DB_PATH = Path(__file__).resolve().parent.parent / "codeshield.db"

def save_scan(scan_id: str, language: str, vuln_count: int, critical_count: int, timestamp: str) -> bool:
    """Creates the scans table if it doesn't exist and inserts a scan record.
    
    Args:
        scan_id (str): Unique identifier for the scan.
        language (str): Programming language detected or used.
        vuln_count (int): Total vulnerabilities found.
        critical_count (int): Number of critical vulnerabilities.
        timestamp (str): ISO-formatted timestamp string of the scan.
        
    Returns:
        bool: True if the operation succeeded, False otherwise.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create scans table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                language TEXT,
                vuln_count INTEGER,
                critical_count INTEGER,
                timestamp TEXT
            )
        """)
        
        # Insert the row
        cursor.execute("""
            INSERT OR REPLACE INTO scans (scan_id, language, vuln_count, critical_count, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (scan_id, language, vuln_count, critical_count, timestamp))
        
        conn.commit()
        conn.close()
        return True
    except Exception:
        # Safe fallback: never crash the app
        return False

def get_recent_scans(limit: int = 5) -> list:
    """Retrieves the last N scans ordered by timestamp descending.
    
    Args:
        limit (int): Maximum number of records to return.
        
    Returns:
        list: A list of dicts representing the scan records, or empty list on failure.
    """
    try:
        if not DB_PATH.exists():
            return []
            
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Verify if table exists before querying
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scans'")
        if not cursor.fetchone():
            conn.close()
            return []
            
        cursor.execute("""
            SELECT scan_id, language, vuln_count, critical_count, timestamp 
            FROM scans 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        
        conn.close()
        return result
    except Exception:
        # Safe fallback: return empty list on failure
        return []
