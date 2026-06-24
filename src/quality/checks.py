import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


class QualityCheck(ABC):
    """Base class for quality checks."""

    def __init__(self, name: str, check_type: str, severity: str):
        """
        Initialize a quality check.

        Args:
            name: Human-readable name for the check
            check_type: Type of check (e.g., 'row_count', 'freshness', 'null_ratio')
            severity: One of 'FAIL' (stop pipeline), 'WARN' (log, continue), 'INFO' (log only)
        """
        self.name = name
        self.check_type = check_type
        self.severity = severity

    @abstractmethod
    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run the quality check on a dataframe.

        Args:
            df: Pandas DataFrame to check

        Returns:
            Dict with keys:
            - passed: bool - whether check passed
            - message: str - human-readable message
            - severity: str - severity level
            - details: dict - additional details about the check result
        """
        pass


class RowCountCheck(QualityCheck):
    """Verify minimum row count in dataframe."""

    def __init__(self, name: str, min_rows: int, severity: str = "FAIL"):
        """
        Initialize row count check.

        Args:
            name: Check name
            min_rows: Minimum required rows
            severity: Severity level
        """
        super().__init__(name, "row_count", severity)
        self.min_rows = min_rows

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check that dataframe has minimum row count."""
        row_count = len(df)
        passed = bool(row_count >= self.min_rows)

        message = (
            f"Row count check PASSED: {row_count} >= {self.min_rows}"
            if passed
            else f"Row count check FAILED: {row_count} < {self.min_rows}"
        )

        return {
            "passed": passed,
            "message": message,
            "severity": self.severity,
            "details": {
                "row_count": row_count,
                "min_rows": self.min_rows,
                "check_name": self.name,
            },
        }


class FreshnessCheck(QualityCheck):
    """Verify data freshness (age in hours)."""

    def __init__(
        self, name: str, max_age_hours: int, timestamp_col: str = "loaded_at", severity: str = "WARN"
    ):
        """
        Initialize freshness check.

        Args:
            name: Check name
            max_age_hours: Maximum age in hours
            timestamp_col: Column name with timestamp data
            severity: Severity level
        """
        super().__init__(name, "freshness", severity)
        self.max_age_hours = max_age_hours
        self.timestamp_col = timestamp_col

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check that data is fresh (not older than max_age_hours)."""
        if self.timestamp_col not in df.columns:
            return {
                "passed": False,
                "message": f"Freshness check FAILED: timestamp column '{self.timestamp_col}' not found",
                "severity": self.severity,
                "details": {
                    "timestamp_col": self.timestamp_col,
                    "available_cols": list(df.columns),
                    "check_name": self.name,
                },
            }

        try:
            # Get the most recent timestamp
            max_timestamp = pd.to_datetime(df[self.timestamp_col]).max()
            now = datetime.utcnow()
            age_hours = (now - max_timestamp).total_seconds() / 3600

            passed = bool(age_hours <= self.max_age_hours)

            message = (
                f"Freshness check PASSED: max age {age_hours:.2f}h <= {self.max_age_hours}h"
                if passed
                else f"Freshness check FAILED: max age {age_hours:.2f}h > {self.max_age_hours}h"
            )

            return {
                "passed": passed,
                "message": message,
                "severity": self.severity,
                "details": {
                    "max_age_hours": self.max_age_hours,
                    "actual_age_hours": round(age_hours, 2),
                    "most_recent_timestamp": str(max_timestamp),
                    "check_name": self.name,
                },
            }

        except Exception as e:
            logger.error(f"Freshness check error: {e}")
            return {
                "passed": False,
                "message": f"Freshness check ERROR: {str(e)}",
                "severity": self.severity,
                "details": {"error": str(e), "check_name": self.name},
            }


class ReferentialIntegrityCheck(QualityCheck):
    """Verify foreign key constraints."""

    def __init__(
        self,
        name: str,
        fk_column: str,
        fk_table: str,
        pk_column: str,
        severity: str = "FAIL",
    ):
        """
        Initialize referential integrity check.

        Args:
            name: Check name
            fk_column: Foreign key column in current dataframe
            fk_table: Name of table with primary key
            pk_column: Primary key column in fk_table
            severity: Severity level
        """
        super().__init__(name, "referential_integrity", severity)
        self.fk_column = fk_column
        self.fk_table = fk_table
        self.pk_column = pk_column

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check referential integrity.

        Note: In MVP, this just checks for non-null FK values.
        Full validation would require database query.
        """
        if self.fk_column not in df.columns:
            return {
                "passed": False,
                "message": f"Referential integrity check FAILED: FK column '{self.fk_column}' not found",
                "severity": self.severity,
                "details": {
                    "fk_column": self.fk_column,
                    "available_cols": list(df.columns),
                    "check_name": self.name,
                },
            }

        # Check for null values in FK (MVP: simplified, no DB lookup)
        null_count = int(df[self.fk_column].isna().sum())
        total_count = len(df)
        passed = bool(null_count == 0)

        message = (
            f"Referential integrity check PASSED: no null FKs in {self.fk_column}"
            if passed
            else f"Referential integrity check FAILED: {null_count}/{total_count} null FKs in {self.fk_column}"
        )

        return {
            "passed": passed,
            "message": message,
            "severity": self.severity,
            "details": {
                "fk_column": self.fk_column,
                "fk_table": self.fk_table,
                "pk_column": self.pk_column,
                "null_count": null_count,
                "total_count": total_count,
                "check_name": self.name,
            },
        }


class NullRatioCheck(QualityCheck):
    """Verify null percentage in columns."""

    def __init__(
        self, name: str, column: str, max_null_ratio: float, severity: str = "WARN"
    ):
        """
        Initialize null ratio check.

        Args:
            name: Check name
            column: Column to check
            max_null_ratio: Maximum allowed null ratio (0.0 to 1.0)
            severity: Severity level
        """
        super().__init__(name, "null_ratio", severity)
        self.column = column
        self.max_null_ratio = max_null_ratio

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check null percentage in column."""
        if self.column not in df.columns:
            return {
                "passed": False,
                "message": f"Null ratio check FAILED: column '{self.column}' not found",
                "severity": self.severity,
                "details": {
                    "column": self.column,
                    "available_cols": list(df.columns),
                    "check_name": self.name,
                },
            }

        null_count = int(df[self.column].isna().sum())
        total_count = len(df)
        null_ratio = null_count / total_count if total_count > 0 else 0

        passed = bool(null_ratio <= self.max_null_ratio)

        message = (
            f"Null ratio check PASSED: {null_ratio:.2%} null in {self.column} <= {self.max_null_ratio:.2%}"
            if passed
            else f"Null ratio check FAILED: {null_ratio:.2%} null in {self.column} > {self.max_null_ratio:.2%}"
        )

        return {
            "passed": passed,
            "message": message,
            "severity": self.severity,
            "details": {
                "column": self.column,
                "null_count": null_count,
                "total_count": total_count,
                "null_ratio": round(null_ratio, 4),
                "max_null_ratio": self.max_null_ratio,
                "check_name": self.name,
            },
        }
