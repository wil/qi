import sys
import tomllib
from pathlib import Path

import pytest

from qi.lib.config import Settings, _user_config_path, load


def test_defaults():
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=Path("/nonexistent/.qi/config.toml"),
    )
    assert s.api_key == ""
    assert s.model == "gpt-4o"
    assert s.base_url == "https://api.openai.com/v1"
    assert s.max_tokens == 4096
    assert s.temperature == 0.0


def test_user_config(tmp_path):
    user_cfg = tmp_path / "user.toml"
    user_cfg.write_text('api_key = "sk-user"')
    s = load(
        user_config=user_cfg,
        project_config=Path("/nonexistent/.qi/config.toml"),
    )
    assert s.api_key == "sk-user"
    assert s.model == "gpt-4o"


def test_project_config(tmp_path):
    proj_cfg = tmp_path / "project.toml"
    proj_cfg.write_text('model = "gpt-4o-mini"')
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=proj_cfg,
    )
    assert s.model == "gpt-4o-mini"


def test_project_overrides_user(tmp_path):
    user_cfg = tmp_path / "user.toml"
    proj_cfg = tmp_path / "project.toml"
    user_cfg.write_text("api_key = \"sk-user\"\nmodel = \"gpt-4o\"")
    proj_cfg.write_text("api_key = \"sk-proj\"")
    s = load(user_config=user_cfg, project_config=proj_cfg)
    assert s.api_key == "sk-proj"
    assert s.model == "gpt-4o"


def test_env_overrides_config(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    cfg.write_text('api_key = "sk-file"\nmodel = "gpt-4o"')
    monkeypatch.setenv("QI_API_KEY", "sk-env")
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=cfg,
    )
    assert s.api_key == "sk-env"
    assert s.model == "gpt-4o"


def test_env_type_coercion(monkeypatch):
    monkeypatch.setenv("QI_MAX_TOKENS", "2048")
    monkeypatch.setenv("QI_TEMPERATURE", "0.5")
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=Path("/nonexistent/.qi/config.toml"),
    )
    assert s.max_tokens == 2048
    assert isinstance(s.max_tokens, int)
    assert s.temperature == 0.5
    assert isinstance(s.temperature, float)


def test_only_qi_env_vars_considered(monkeypatch):
    monkeypatch.setenv("QI_API_KEY", "sk-ok")
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("HOME", "/home/test")
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=Path("/nonexistent/.qi/config.toml"),
    )
    assert s.api_key == "sk-ok"


def test_missing_files_ignored():
    """Non-existent paths should be silently skipped."""
    s = load(
        user_config=Path("/nonexistent/user.toml"),
        project_config=Path("/nonexistent/project.toml"),
    )
    assert s.model == "gpt-4o"


def test_partial_config_keeps_defaults(tmp_path):
    user_cfg = tmp_path / "user.toml"
    user_cfg.write_text("temperature = 0.7")
    s = load(
        user_config=user_cfg,
        project_config=Path("/nonexistent/.qi/config.toml"),
    )
    assert s.temperature == 0.7
    assert s.model == "gpt-4o"
    assert s.max_tokens == 4096


def test_malformed_toml_raises(tmp_path):
    cfg = tmp_path / "bad.toml"
    cfg.write_text("[[[[broken")
    with pytest.raises(tomllib.TOMLDecodeError):
        load(
            user_config=cfg,
            project_config=Path("/nonexistent/.qi/config.toml"),
        )


def test_openai_section_supported(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text("[openai]\napi_key = \"sk-section\"")
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=cfg,
    )
    assert s.api_key == "sk-section"


def test_flat_toml_still_works(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text("api_key = \"sk-flat\"")
    s = load(
        user_config=Path("/nonexistent/config.toml"),
        project_config=cfg,
    )
    assert s.api_key == "sk-flat"


def test_empty_user_config_ignored(tmp_path):
    cfg = tmp_path / "empty.toml"
    cfg.write_text("")
    s = load(
        user_config=cfg,
        project_config=Path("/nonexistent/.qi/config.toml"),
    )
    assert s.api_key == ""
    assert s.model == "gpt-4o"


def test_settings_dataclass():
    s = Settings()
    assert s.api_key == ""
    assert s.model == "gpt-4o"


def test_user_config_path_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = _user_config_path()
    assert path == Path.home() / ".config" / "qi" / "config.toml"


def test_user_config_path_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    path = _user_config_path()
    assert path == Path("/custom/config/qi/config.toml")


def test_user_config_path_windows_appdata(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\test\AppData\Roaming")
    path = _user_config_path()
    assert path == Path(r"C:\Users\test\AppData\Roaming") / "qi" / "config.toml"


def test_user_config_path_windows_fallback(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    path = _user_config_path()
    assert path == Path.home() / "AppData" / "Roaming" / "qi" / "config.toml"
