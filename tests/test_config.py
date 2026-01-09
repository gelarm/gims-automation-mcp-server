"""Tests for configuration module."""

from gims_mcp.config import Config, _parse_bool_env


class TestParseBoolEnv:
    """Tests for _parse_bool_env helper function."""

    def test_none_returns_default_true(self):
        """None value returns default True."""
        assert _parse_bool_env(None) is True

    def test_none_returns_default_false(self):
        """None value returns specified default."""
        assert _parse_bool_env(None, default=False) is False

    def test_false_values(self):
        """Test various false values."""
        for value in ("false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF"):
            assert _parse_bool_env(value) is False

    def test_true_values(self):
        """Test various true values."""
        for value in ("true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON"):
            assert _parse_bool_env(value) is True

    def test_unknown_values_treated_as_true(self):
        """Unknown values are treated as True (safe default for SSL)."""
        # Any non-false value enables SSL verification for security
        assert _parse_bool_env("maybe") is True
        assert _parse_bool_env("enabled") is True


class TestConfigFromArgs:
    """Tests for Config.from_args method."""

    def test_verify_ssl_default_true(self, monkeypatch):
        """verify_ssl defaults to True."""
        monkeypatch.delenv("GIMS_VERIFY_SSL", raising=False)
        config = Config.from_args(url="https://example.com", token="test-token")
        assert config.verify_ssl is True

    def test_verify_ssl_from_env_false(self, monkeypatch):
        """verify_ssl from env variable."""
        monkeypatch.setenv("GIMS_VERIFY_SSL", "false")
        config = Config.from_args(url="https://example.com", token="test-token")
        assert config.verify_ssl is False

    def test_verify_ssl_from_env_zero(self, monkeypatch):
        """verify_ssl=0 from env variable."""
        monkeypatch.setenv("GIMS_VERIFY_SSL", "0")
        config = Config.from_args(url="https://example.com", token="test-token")
        assert config.verify_ssl is False

    def test_verify_ssl_cli_overrides_env(self, monkeypatch):
        """CLI argument overrides env variable."""
        monkeypatch.setenv("GIMS_VERIFY_SSL", "true")
        config = Config.from_args(url="https://example.com", token="test-token", verify_ssl=False)
        assert config.verify_ssl is False

    def test_verify_ssl_cli_true(self, monkeypatch):
        """CLI argument verify_ssl=True."""
        monkeypatch.setenv("GIMS_VERIFY_SSL", "false")
        config = Config.from_args(url="https://example.com", token="test-token", verify_ssl=True)
        assert config.verify_ssl is True


class TestConfigFromEnv:
    """Tests for Config.from_env method."""

    def test_verify_ssl_default_true(self, monkeypatch):
        """verify_ssl defaults to True."""
        monkeypatch.setenv("GIMS_URL", "https://example.com")
        monkeypatch.setenv("GIMS_TOKEN", "test-token")
        monkeypatch.delenv("GIMS_VERIFY_SSL", raising=False)
        config = Config.from_env()
        assert config.verify_ssl is True

    def test_verify_ssl_false(self, monkeypatch):
        """verify_ssl=false from env."""
        monkeypatch.setenv("GIMS_URL", "https://example.com")
        monkeypatch.setenv("GIMS_TOKEN", "test-token")
        monkeypatch.setenv("GIMS_VERIFY_SSL", "false")
        config = Config.from_env()
        assert config.verify_ssl is False

    def test_verify_ssl_zero(self, monkeypatch):
        """verify_ssl=0 from env."""
        monkeypatch.setenv("GIMS_URL", "https://example.com")
        monkeypatch.setenv("GIMS_TOKEN", "test-token")
        monkeypatch.setenv("GIMS_VERIFY_SSL", "0")
        config = Config.from_env()
        assert config.verify_ssl is False
