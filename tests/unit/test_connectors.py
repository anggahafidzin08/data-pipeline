import pytest
from unittest.mock import Mock, patch, MagicMock
from src.common.connectors import SupabaseClient, get_supabase_client
from src.common.exceptions import DatabaseError


def mock_settings():
    """Create mock settings object."""
    mock = Mock()
    mock.supabase_url = "https://test-project.supabase.co"
    mock.supabase_key = "test-key"
    mock.log_level = "INFO"
    return mock


class TestSupabaseClientSingleton:
    """Test that SupabaseClient is a singleton."""

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_singleton_instance(self, mock_connect, mock_get_settings):
        """Test that multiple calls return the same instance."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        client1 = SupabaseClient()
        client2 = SupabaseClient()

        assert client1 is client2, "SupabaseClient should be a singleton"

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_get_supabase_client_returns_singleton(self, mock_connect, mock_get_settings):
        """Test that get_supabase_client returns singleton."""
        # Reset singleton for test
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        client1 = get_supabase_client()
        client2 = get_supabase_client()

        assert client1 is client2, "get_supabase_client should return singleton"


class TestExecuteQuery:
    """Test execute_query method."""

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_execute_query_returns_list_of_dicts(self, mock_connect, mock_get_settings):
        """Test that execute_query returns list of dicts."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"id": "1", "name": "Product1"},
            {"id": "2", "name": "Product2"},
        ]
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SupabaseClient()
        result = client.execute_query("SELECT * FROM products", None)

        assert isinstance(result, list), "Result should be a list"
        assert len(result) == 2, "Result should have 2 items"
        assert result[0]["name"] == "Product1", "First item should have correct data"

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_execute_query_with_params(self, mock_connect, mock_get_settings):
        """Test execute_query with parameters."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": "1", "name": "Product1"}]
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SupabaseClient()
        result = client.execute_query("SELECT * FROM products WHERE id = %s", ("1",))

        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM products WHERE id = %s", ("1",)
        )
        assert len(result) == 1

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_execute_query_raises_database_error_on_failure(self, mock_connect, mock_get_settings):
        """Test that execute_query raises DatabaseError on failure."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor to raise exception
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Connection lost")
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SupabaseClient()

        with pytest.raises(DatabaseError):
            client.execute_query("SELECT * FROM products", None)


class TestExecuteUpdate:
    """Test execute_update method."""

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_execute_update_returns_affected_rows(self, mock_connect, mock_get_settings):
        """Test that execute_update returns affected row count."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SupabaseClient()
        result = client.execute_update("INSERT INTO products VALUES (%s)", ("Product1",))

        assert result == 3, "Should return 3 affected rows"
        mock_conn.commit.assert_called_once()

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_execute_update_raises_database_error_on_failure(self, mock_connect, mock_get_settings):
        """Test that execute_update raises DatabaseError on failure."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor to raise exception
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Constraint violation")
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SupabaseClient()

        with pytest.raises(DatabaseError):
            client.execute_update("INSERT INTO products VALUES (%s)", ("Product1",))

        mock_conn.rollback.assert_called_once()


class TestInsertRows:
    """Test insert_rows method."""

    @patch("src.common.connectors.execute_batch")
    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_insert_rows_batch_insert(self, mock_connect, mock_get_settings, mock_execute_batch):
        """Test batch insert of multiple rows."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 3
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock execute_batch to do nothing
        mock_execute_batch.return_value = None

        client = SupabaseClient()
        rows = [
            {"id": "1", "name": "Product1"},
            {"id": "2", "name": "Product2"},
            {"id": "3", "name": "Product3"},
        ]
        result = client.insert_rows("products", rows)

        assert result == 3, "Should return 3 rows inserted"
        mock_conn.commit.assert_called_once()
        mock_execute_batch.assert_called_once()

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_insert_rows_empty_list(self, mock_connect, mock_get_settings):
        """Test insert_rows with empty list."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        client = SupabaseClient()
        result = client.insert_rows("products", [])

        assert result == 0, "Should return 0 for empty list"
        mock_conn.commit.assert_not_called()

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_insert_rows_raises_database_error_on_failure(self, mock_connect, mock_get_settings):
        """Test that insert_rows raises DatabaseError on failure."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()

        # Mock cursor to raise exception
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Patch execute_batch to raise exception
        with patch("src.common.connectors.execute_batch") as mock_execute_batch:
            mock_execute_batch.side_effect = Exception("Batch insert failed")

            client = SupabaseClient()
            rows = [{"id": "1", "name": "Product1"}]

            with pytest.raises(DatabaseError):
                client.insert_rows("products", rows)

            mock_conn.rollback.assert_called_once()


class TestDatabaseErrorHandling:
    """Test exception handling."""

    @patch("src.common.connectors.get_settings")
    @patch("src.common.connectors.psycopg2.connect")
    def test_connection_failure_raises_database_error(self, mock_connect, mock_get_settings):
        """Test that connection failure raises DatabaseError."""
        # Reset singleton
        SupabaseClient._instance = None
        SupabaseClient._connection = None

        mock_get_settings.return_value = mock_settings()
        mock_connect.side_effect = Exception("Connection refused")

        with pytest.raises(DatabaseError) as exc_info:
            SupabaseClient()

        assert "Connection failed" in str(exc_info.value)
