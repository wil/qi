"""Configuration management for Qi.

Config hierarchy (highest to lowest priority):
  1. QI_* environment variables
  2. .qi/config.toml (project-level)
  3. User config dir (platform-dependent, see _user_config_path)
  4. Hardcoded defaults
"""

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


def _user_config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "qi" / "config.toml"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "qi" / "config.toml"
    return Path.home() / ".config" / "qi" / "config.toml"


@dataclass
class Settings:
    api_key: str = ""
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    max_tokens: int = 4096
    temperature: float = 0.0


_ENV_PREFIX = "QI_"

_FIELD_TYPES: dict[str, type] = {
    "api_key": str,
    "model": str,
    "base_url": str,
    "max_tokens": int,
    "temperature": float,
}


def load(
    user_config: Path | None = None,
    project_config: Path | None = None,
) -> Settings:
    s = Settings()

    path = user_config or _user_config_path()
    _merge_toml(s, path)

    path = project_config or Path.cwd() / ".qi" / "config.toml"
    _merge_toml(s, path)

    _merge_env(s)

    return s


def _merge_toml(s: Settings, path: Path) -> None:
    if not path.exists():
        return
    with path.open("rb") as f:
        data = tomllib.load(f)

    if "openai" in data and isinstance(data["openai"], dict):
        data = data["openai"]

    for key, val in data.items():
        if key in _FIELD_TYPES:
            setattr(s, key, val)


def _merge_env(s: Settings) -> None:
    prefix_len = len(_ENV_PREFIX)
    for env_key, env_val in os.environ.items():
        if not env_key.startswith(_ENV_PREFIX):
            continue
        attr = env_key[prefix_len:].lower()
        if attr not in _FIELD_TYPES:
            continue
        ftype = _FIELD_TYPES[attr]
        coerced: str | int | float = env_val
        if ftype is int:
            coerced = int(env_val)
        elif ftype is float:
            coerced = float(env_val)
        setattr(s, attr, coerced)
