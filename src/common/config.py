import os
from typing import Optional
import yaml
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Settings:
    """Load settings from environment variables and YAML config files."""

    def __init__(self, env: str = "dev"):
        self.env = env
        self._load_secrets_from_env()
        self._load_config_from_yaml()

    def _load_secrets_from_env(self):
        """Secrets ONLY from environment variables."""
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        self.supabase_key: str = os.getenv("SUPABASE_KEY", "")
        self.source_url: str = os.getenv("SOURCE_URL", "")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

    def _load_config_from_yaml(self):
        """Load non-sensitive config from YAML files."""
        base_path = os.path.join(os.path.dirname(__file__), "../../conf/base.yaml")
        env_path = os.path.join(os.path.dirname(__file__), f"../../conf/{self.env}.yaml")

        # Load base config
        with open(base_path, 'r') as f:
            base_config = yaml.safe_load(f) or {}

        # Load environment-specific overrides
        env_config = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_config = yaml.safe_load(f) or {}

        # Merge configs
        merged = {**base_config, **env_config}

        # Set attributes
        self.log_level: str = merged.get("pipeline", {}).get("log_level", "INFO")
        self.pipeline_name: str = merged.get("pipeline", {}).get("pipeline_name", "ecommerce_pipeline")
        self.source_id: str = merged.get("pipeline", {}).get("source_id", "ecommerce_site")
        self.scraper: dict = merged.get("scraper", {})
        self.data_contracts: dict = merged.get("data_contracts", {})
        self.scd2_config: dict = merged.get("scd2_config", {})

# Singleton instance
_settings: Optional[Settings] = None

def get_settings(env: str = "dev") -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings(env)
    return _settings
