import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.quality.checks import (
    RowCountCheck,
    FreshnessCheck,
    ReferentialIntegrityCheck,
    NullRatioCheck,
)
from src.quality.runner import QualityCheckRunner


class TestRowCountCheck:
    """Tests for RowCountCheck."""

    def test_row_count_check_pass(self):
        """Test that RowCountCheck passes when row count meets minimum."""
        df = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})
        check = RowCountCheck("test_check", min_rows=5)

        result = check.run(df)

        assert result["passed"] is True
        assert "PASSED" in result["message"]
        assert result["details"]["row_count"] == 5
        assert result["details"]["min_rows"] == 5

    def test_row_count_check_fail(self):
        """Test that RowCountCheck fails when row count below minimum."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        check = RowCountCheck("test_check", min_rows=10)

        result = check.run(df)

        assert result["passed"] is False
        assert "FAILED" in result["message"]
        assert result["details"]["row_count"] == 3
        assert result["details"]["min_rows"] == 10

    def test_row_count_check_empty_dataframe(self):
        """Test RowCountCheck on empty dataframe."""
        df = pd.DataFrame()
        check = RowCountCheck("test_check", min_rows=100)

        result = check.run(df)

        assert result["passed"] is False
        assert result["details"]["row_count"] == 0

    def test_row_count_check_severity(self):
        """Test that severity is preserved in result."""
        df = pd.DataFrame({"col1": [1]})
        check_fail = RowCountCheck("test", min_rows=10, severity="FAIL")
        check_warn = RowCountCheck("test", min_rows=10, severity="WARN")

        assert check_fail.run(df)["severity"] == "FAIL"
        assert check_warn.run(df)["severity"] == "WARN"


class TestFreshnessCheck:
    """Tests for FreshnessCheck."""

    def test_freshness_check_pass(self):
        """Test FreshnessCheck passes for recent data."""
        now = datetime.utcnow()
        recent_time = now - timedelta(hours=1)

        df = pd.DataFrame({"loaded_at": [recent_time, recent_time]})
        check = FreshnessCheck("test_check", max_age_hours=24)

        result = check.run(df)

        assert result["passed"] is True
        assert "PASSED" in result["message"]
        assert result["details"]["max_age_hours"] == 24
        assert result["details"]["actual_age_hours"] < 2  # Less than 2 hours old

    def test_freshness_check_fail(self):
        """Test FreshnessCheck fails for old data."""
        old_time = datetime.utcnow() - timedelta(hours=30)

        df = pd.DataFrame({"loaded_at": [old_time]})
        check = FreshnessCheck("test_check", max_age_hours=24)

        result = check.run(df)

        assert result["passed"] is False
        assert "FAILED" in result["message"]
        assert result["details"]["actual_age_hours"] > 24

    def test_freshness_check_missing_column(self):
        """Test FreshnessCheck handles missing timestamp column."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        check = FreshnessCheck("test_check", max_age_hours=24, timestamp_col="loaded_at")

        result = check.run(df)

        assert result["passed"] is False
        assert "not found" in result["message"].lower()

    def test_freshness_check_custom_column(self):
        """Test FreshnessCheck with custom timestamp column name."""
        now = datetime.utcnow()
        recent_time = now - timedelta(hours=1)

        df = pd.DataFrame({"scraped_at": [recent_time]})
        check = FreshnessCheck("test_check", max_age_hours=24, timestamp_col="scraped_at")

        result = check.run(df)

        assert result["passed"] is True


class TestReferentialIntegrityCheck:
    """Tests for ReferentialIntegrityCheck."""

    def test_referential_integrity_check_pass(self):
        """Test ReferentialIntegrityCheck passes when no nulls in FK."""
        df = pd.DataFrame({"product_id": [1, 2, 3, 4, 5]})
        check = ReferentialIntegrityCheck(
            "test_check", "product_id", "products", "id"
        )

        result = check.run(df)

        assert result["passed"] is True
        assert "PASSED" in result["message"]
        assert result["details"]["null_count"] == 0

    def test_referential_integrity_check_fail(self):
        """Test ReferentialIntegrityCheck fails when nulls in FK."""
        df = pd.DataFrame({"product_id": [1, 2, None, 4, None]})
        check = ReferentialIntegrityCheck(
            "test_check", "product_id", "products", "id"
        )

        result = check.run(df)

        assert result["passed"] is False
        assert "FAILED" in result["message"]
        assert result["details"]["null_count"] == 2
        assert result["details"]["total_count"] == 5

    def test_referential_integrity_check_missing_column(self):
        """Test ReferentialIntegrityCheck handles missing FK column."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        check = ReferentialIntegrityCheck(
            "test_check", "product_id", "products", "id"
        )

        result = check.run(df)

        assert result["passed"] is False
        assert "not found" in result["message"].lower()


class TestNullRatioCheck:
    """Tests for NullRatioCheck."""

    def test_null_ratio_check_pass(self):
        """Test NullRatioCheck passes when null ratio below threshold."""
        df = pd.DataFrame({"price": [100.0, 200.0, None, 400.0, 500.0]})
        check = NullRatioCheck("test_check", "price", max_null_ratio=0.25)

        result = check.run(df)

        assert result["passed"] is True
        assert "PASSED" in result["message"]
        assert result["details"]["null_ratio"] == 0.2  # 1/5 = 0.2

    def test_null_ratio_check_fail(self):
        """Test NullRatioCheck fails when null ratio exceeds threshold."""
        df = pd.DataFrame({"price": [100.0, None, None, None, 500.0]})
        check = NullRatioCheck("test_check", "price", max_null_ratio=0.25)

        result = check.run(df)

        assert result["passed"] is False
        assert "FAILED" in result["message"]
        assert result["details"]["null_ratio"] == 0.6  # 3/5 = 0.6

    def test_null_ratio_check_no_nulls(self):
        """Test NullRatioCheck passes when no nulls."""
        df = pd.DataFrame({"price": [100.0, 200.0, 300.0, 400.0, 500.0]})
        check = NullRatioCheck("test_check", "price", max_null_ratio=0.1)

        result = check.run(df)

        assert result["passed"] is True
        assert result["details"]["null_ratio"] == 0.0

    def test_null_ratio_check_all_nulls(self):
        """Test NullRatioCheck with all nulls."""
        df = pd.DataFrame({"price": [None, None, None, None, None]})
        check = NullRatioCheck("test_check", "price", max_null_ratio=0.5)

        result = check.run(df)

        assert result["passed"] is False
        assert result["details"]["null_ratio"] == 1.0

    def test_null_ratio_check_missing_column(self):
        """Test NullRatioCheck handles missing column."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        check = NullRatioCheck("test_check", "price", max_null_ratio=0.1)

        result = check.run(df)

        assert result["passed"] is False
        assert "not found" in result["message"].lower()


class TestQualityCheckRunner:
    """Tests for QualityCheckRunner."""

    def test_runner_initialization_with_config(self):
        """Test QualityCheckRunner initializes with config."""
        config = {
            "bronze": {
                "raw_products": {
                    "checks": [
                        {"type": "row_count", "min_rows": 100, "severity": "FAIL"}
                    ]
                }
            }
        }

        runner = QualityCheckRunner(config)

        assert runner.config == config

    def test_runner_run_checks_row_count(self):
        """Test runner executing row count checks."""
        config = {
            "bronze": {
                "raw_products": {
                    "checks": [
                        {"type": "row_count", "min_rows": 5, "severity": "FAIL"}
                    ]
                }
            }
        }

        runner = QualityCheckRunner(config)
        df = pd.DataFrame({"col": [1, 2, 3, 4, 5]})

        results = runner.run_checks("bronze", df)

        assert len(results) == 1
        assert results[0]["passed"] is True

    def test_runner_run_checks_multiple(self):
        """Test runner executing multiple checks."""
        config = {
            "silver": {
                "products_clean": {
                    "checks": [
                        {"type": "row_count", "min_rows": 5, "severity": "FAIL"},
                        {
                            "type": "null_ratio",
                            "column": "price",
                            "max_null_ratio": 0.1,
                            "severity": "WARN",
                        },
                    ]
                }
            }
        }

        runner = QualityCheckRunner(config)
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "price": [100.0, 200.0, 300.0, 400.0, None],
            }
        )

        results = runner.run_checks("silver", df)

        assert len(results) == 2
        assert results[0]["passed"] is True  # Row count check
        assert results[1]["passed"] is False  # Null ratio check (1/5 = 0.2 > 0.1 threshold, fails)

    def test_runner_aggregate_results(self):
        """Test aggregation of check results."""
        config = {
            "bronze": {
                "raw_products": {
                    "checks": [
                        {"type": "row_count", "min_rows": 100, "severity": "FAIL"},
                        {"type": "row_count", "min_rows": 5, "severity": "WARN"},
                    ]
                }
            }
        }

        runner = QualityCheckRunner(config)
        df = pd.DataFrame({"col": [1, 2, 3, 4, 5]})

        results = runner.run_checks("bronze", df)
        summary = runner.aggregate_results(results)

        assert summary["total_checks"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["by_severity"]["FAIL"] >= 1
        assert summary["by_severity"]["WARN"] >= 1

    def test_runner_unknown_layer(self):
        """Test runner handles unknown layer gracefully."""
        config = {"bronze": {"raw_products": {"checks": []}}}

        runner = QualityCheckRunner(config)
        df = pd.DataFrame({"col": [1, 2, 3]})

        results = runner.run_checks("unknown_layer", df)

        assert len(results) == 0

    def test_runner_build_check_unknown_type(self):
        """Test runner handles unknown check type."""
        config = {
            "bronze": {
                "raw_products": {
                    "checks": [{"type": "unknown_type", "severity": "FAIL"}]
                }
            }
        }

        runner = QualityCheckRunner(config)
        df = pd.DataFrame({"col": [1, 2, 3]})

        results = runner.run_checks("bronze", df)

        # Unknown type should not produce a check result (logged as warning)
        assert len(results) == 0

    def test_runner_build_check_incomplete_config(self):
        """Test runner handles incomplete check configuration."""
        config = {
            "bronze": {
                "raw_products": {
                    "checks": [
                        {
                            "type": "referential_integrity",
                            "severity": "FAIL",
                            # missing fk_column, fk_table, pk_column
                        }
                    ]
                }
            }
        }

        runner = QualityCheckRunner(config)
        df = pd.DataFrame({"col": [1, 2, 3]})

        results = runner.run_checks("bronze", df)

        # Incomplete config should not produce a check result
        assert len(results) == 0

    def test_runner_freshness_check_integration(self):
        """Test runner with freshness checks."""
        now = datetime.utcnow()
        recent_time = now - timedelta(hours=1)

        config = {
            "bronze": {
                "raw_products": {
                    "checks": [
                        {
                            "type": "freshness",
                            "max_age_hours": 24,
                            "timestamp_col": "loaded_at",
                            "severity": "WARN",
                        }
                    ]
                }
            }
        }

        runner = QualityCheckRunner(config)
        df = pd.DataFrame({"loaded_at": [recent_time, recent_time]})

        results = runner.run_checks("bronze", df)

        assert len(results) == 1
        assert results[0]["passed"] is True
