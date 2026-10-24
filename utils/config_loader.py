import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_CONFIG_PATH = PROJECT_ROOT / "config" / "env.yaml"
PAYTABLE_PATH = PROJECT_ROOT / "config" / "paytable.yaml"


def load_config(env: str = "qa") -> dict:
    """Load the named environment block from config/env.yaml, with GAME_URL
    and PLAYER_TOKEN overridable from a local .env file."""
    load_dotenv(PROJECT_ROOT / ".env")

    with open(ENV_CONFIG_PATH, "r", encoding="utf-8") as f:
        all_envs = yaml.safe_load(f)

    if env not in all_envs:
        raise KeyError(f"Environment '{env}' not found in {ENV_CONFIG_PATH}")

    config = all_envs[env]
    config["game_url"] = os.getenv("GAME_URL") or config.get("game_url")
    config["player_token"] = os.getenv("PLAYER_TOKEN")
    return config


def load_paytable() -> dict:
    """Load the static paytable reference data from config/paytable.yaml."""
    with open(PAYTABLE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
