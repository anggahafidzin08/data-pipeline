import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from src.common.config import get_settings
from src.quality.checks import (
    QualityCheck,
    RowCountCheck,
    FreshnessCheck,
    ReferentialIntegrityCheck,
    NullRatioCheck,
)

logger = logging.getLogger(__name__)


class QualityCheckRunner:
    """Orchestrator for running quality checks on data layers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize quality check runner.

        Args:
            config: Configuration dict with data_contracts (from settings)
        """
        if config is None:
            settings = get_settings()
            self.config = settings.data_contracts
        else:
            self.config = config

    def run_checks(self, layer: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Run all configured checks for a layer.

        Args:
            layer: Layer name ('bronze', 'silver', 'gold')
            df: DataFrame to check

        Returns:
            List of check results, each with:
            - passed: bool
            - message: str
            - severity: str
            - details: dict
        """
        results = []

        # Get layer config
        layer_config = self.config.get(layer, {})

        if not layer_config:
            logger.warning(f"No quality contract found for layer: {layer}")
            return results

        # Process each table in layer
        for table_name, table_config in layer_config.items():
            logger.info(f"Running quality checks for {layer}.{table_name}")

            # Get checks from config
            checks = table_config.get("checks", [])

            for check_config in checks:
                try:
                    check = self._build_check(check_config, table_name)
                    if check:
                        result = check.run(df)
                        results.append(result)
                        self._log_result(result)
                except Exception as e:
                    logger.error(f"Failed to run check: {e}")
                    results.append(
                        {
                            "passed": False,
                            "message": f"Check execution failed: {str(e)}",
                            "severity": "FAIL",
                            "details": {"error": str(e), "table": table_name},
                        }
                    )

        return results

    def _build_check(self, check_config: Dict[str, Any], table_name: str) -> Optional[QualityCheck]:
        """
        Build a quality check from configuration.

        Args:
            check_config: Check configuration dict
            table_name: Name of table being checked

        Returns:
            QualityCheck instance or None if build failed
        """
        check_type = check_config.get("type")
        severity = check_config.get("severity", "FAIL")
        check_name = f"{table_name}_{check_type}"

        try:
            if check_type == "row_count":
                min_rows = check_config.get("min_rows", 0)
                return RowCountCheck(check_name, min_rows, severity)

            elif check_type == "freshness":
                max_age_hours = check_config.get("max_age_hours", 24)
                timestamp_col = check_config.get("timestamp_col", "loaded_at")
                return FreshnessCheck(check_name, max_age_hours, timestamp_col, severity)

            elif check_type == "referential_integrity":
                fk_column = check_config.get("fk_column")
                fk_table = check_config.get("fk_table")
                pk_column = check_config.get("pk_column")
                if fk_column and fk_table and pk_column:
                    return ReferentialIntegrityCheck(
                        check_name, fk_column, fk_table, pk_column, severity
                    )
                else:
                    logger.warning(
                        f"Incomplete referential_integrity config for {check_name}"
                    )
                    return None

            elif check_type == "null_ratio":
                column = check_config.get("column")
                max_null_ratio = check_config.get("max_null_ratio", 0.1)
                if column:
                    return NullRatioCheck(check_name, column, max_null_ratio, severity)
                else:
                    logger.warning(f"Missing column in null_ratio config for {check_name}")
                    return None

            else:
                logger.warning(f"Unknown check type: {check_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to build check {check_name}: {e}")
            return None

    def _log_result(self, result: Dict[str, Any]):
        """Log a check result at appropriate level."""
        severity = result.get("severity", "INFO")
        message = result.get("message", "")
        passed = result.get("passed", False)

        if severity == "FAIL":
            if passed:
                logger.info(message)
            else:
                logger.error(message)
        elif severity == "WARN":
            if passed:
                logger.info(message)
            else:
                logger.warning(message)
        else:  # INFO
            logger.info(message)

    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate check results.

        Args:
            results: List of check results

        Returns:
            Aggregated summary dict with counts by severity and status
        """
        summary = {
            "total_checks": len(results),
            "passed": 0,
            "failed": 0,
            "by_severity": {"FAIL": 0, "WARN": 0, "INFO": 0},
            "failures": [],
            "warnings": [],
        }

        for result in results:
            if result.get("passed"):
                summary["passed"] += 1
            else:
                summary["failed"] += 1
                if result.get("severity") == "FAIL":
                    summary["failures"].append(result.get("message", ""))
                elif result.get("severity") == "WARN":
                    summary["warnings"].append(result.get("message", ""))

            severity = result.get("severity", "INFO")
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1

        return summary
