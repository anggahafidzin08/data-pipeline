import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from typing import List, Dict, Any, Optional
from src.common.config import get_settings
from src.common.exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Singleton client for Supabase PostgreSQL connection."""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connect()

    def _connect(self):
        """Establish connection to Supabase PostgreSQL."""
        try:
            settings = get_settings()
            # Parse Supabase URL to extract connection details
            # Format: https://project.supabase.co
            url = settings.supabase_url
            if url.startswith("https://"):
                project_id = url.replace("https://", "").split(".")[0]
            else:
                project_id = url.split(".")[0]

            # Note: For now, using direct postgres connection.
            # In production, would use Supabase REST API or psycopg2 with proper credentials.
            # This is a placeholder that will be updated with actual Supabase auth.

            self._connection = psycopg2.connect(
                host=f"{project_id}.supabase.co",
                port=5432,
                database="postgres",
                user="postgres",
                password=settings.supabase_key
            )
            logger.info("Connected to Supabase PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise DatabaseError(f"Connection failed: {e}")

    def execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dicts."""
        try:
            with self._connection.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise DatabaseError(f"Query execution failed: {e}")

    def execute_update(self, sql: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected row count."""
        try:
            with self._connection.cursor() as cur:
                cur.execute(sql, params)
                self._connection.commit()
                return cur.rowcount
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Update failed: {e}")
            raise DatabaseError(f"Update failed: {e}")

    def insert_rows(self, table: str, rows: List[Dict[str, Any]]) -> int:
        """Batch insert rows into table."""
        if not rows:
            return 0

        try:
            columns = list(rows[0].keys())
            placeholders = ", ".join(["%s"] * len(columns))
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

            values = [[row.get(col) for col in columns] for row in rows]

            with self._connection.cursor() as cur:
                execute_batch(cur, sql, values)
                self._connection.commit()
                return cur.rowcount
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Batch insert failed: {e}")
            raise DatabaseError(f"Batch insert failed: {e}")

    def close(self):
        """Close connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

def get_supabase_client() -> SupabaseClient:
    """Get singleton Supabase client."""
    return SupabaseClient()
