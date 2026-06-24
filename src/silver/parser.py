import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SpecParser:
    """Parse product specification string into structured fields."""

    @staticmethod
    def parse(spec: Optional[str]) -> Dict[str, str]:
        """
        Parse spec string into fields.
        Example: "15.6\", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1"
        Returns: {
            "screen_size": "15.6\"",
            "cpu_type": "AMD E2-3800 1.3GHz",
            "builtin_ram": "4GB",
            "builtin_memory": "500GB",
            "operating_system": "Windows 8.1"
        }
        """
        result = {
            "screen_size": "Unknown",
            "cpu_type": "Unknown",
            "builtin_ram": "Unknown",
            "builtin_memory": "Unknown",
            "operating_system": "Unknown"
        }

        if not spec:
            return result

        # Try regex-based parsing first
        try:
            # Screen size: e.g., "15.6\""
            screen_match = re.search(r'(\d+\.?\d*)"', spec)
            if screen_match:
                result["screen_size"] = screen_match.group(0)

            # CPU type: e.g., "AMD E2-3800 1.3GHz", "Core i5-4300U", "Pentium N3520 2.16GHz"
            # Match CPU vendors followed by model and optional frequency
            cpu_match = re.search(
                r'(AMD|Intel|Core|Pentium)[\s\w\-0-9\.]*(?:GHz)?',
                spec,
                re.IGNORECASE
            )
            if cpu_match:
                cpu_str = cpu_match.group(0).strip()
                # Find the full CPU string - get it until next comma or major word boundary
                cpu_start = cpu_match.start()
                cpu_end = spec.find(',', cpu_start)
                if cpu_end == -1:
                    cpu_end = len(spec)
                result["cpu_type"] = spec[cpu_start:cpu_end].strip()

            # RAM: first occurrence of XGB (not followed by TB or other letters except "SSD", "HDD", etc.)
            gb_matches = re.finditer(r'(\d+)\s*(GB|TB)', spec)
            gb_list = list(gb_matches)
            if gb_list:
                # First match is typically RAM
                first_match = gb_list[0]
                result["builtin_ram"] = first_match.group(0)

                # Storage: if there are multiple GB/TB entries, take the last one
                if len(gb_list) > 1:
                    result["builtin_memory"] = gb_list[-1].group(0)

            # Operating System: e.g., "Windows 8.1", "Linux", "Win7 Pro 64bit"
            os_match = re.search(
                r'(Windows|Linux|macOS|Mac OS X|Win7|Win10|Win11)[\s\w0-9\.]*',
                spec,
                re.IGNORECASE
            )
            if os_match:
                result["operating_system"] = os_match.group(0)

        except Exception as e:
            logger.warning(f"Regex parsing failed: {e}. Falling back to position-based parsing.")
            return SpecParser._parse_position_based(spec, result)

        return result

    @staticmethod
    def _parse_position_based(spec: str, result: Dict[str, str]) -> Dict[str, str]:
        """Fallback: position-based parsing assuming comma-separated format."""
        parts = [p.strip() for p in spec.split(",")]

        if len(parts) >= 1 and '"' in parts[0]:
            result["screen_size"] = parts[0]
        if len(parts) >= 2:
            result["cpu_type"] = parts[1]
        if len(parts) >= 3:
            result["builtin_ram"] = parts[2]
        if len(parts) >= 4:
            result["builtin_memory"] = parts[3]
        if len(parts) >= 5:
            result["operating_system"] = parts[4]

        return result
