from __future__ import annotations

from typing import Any
from impala.dbapi import connect
from app.tools.config import settings

def _get_connection():
    """Establishes an authenticated connection channel to the Cloudera Impala database."""
    return connect(
        host=settings.impala_host,
        port=settings.impala_port,
        database=settings.db_name,
        user=settings.cdp_user,
        password=settings.cdp_pass,
        use_ssl=True,
        auth_mechanism="PLAIN",
        http_path=settings.impala_http_path,
        use_http_transport=True,
    )

def execute_query(sql: str) -> dict[str, Any]:
    """
    Executes a read-only query on Cloudera Impala and returns 
    columns, formatted row dictionary maps, and total row count.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Safely extract table headers from the query description matrix
        columns = [desc[0] for desc in cursor.description or []]
        
        # Zip key-value column and row tuples into standard JSON-compatible objects
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    finally:
        conn.close()