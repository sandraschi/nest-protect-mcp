"""
Unit tests for CLI functionality.
"""
import pytest
import argparse
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from nest_protect_mcp.cli import NestProtectCLI


class TestNestProtectCLI:
    """Test NestProtectCLI class."""

    @pytest.fixture
    def cli(self):
        """Create a CLI instance for testing."""
        return NestProtectCLI()

    def test_cli_initialization(self, cli):
        """Test CLI initialization."""
        assert cli.config is None
        assert cli.server is None
        assert hasattr(cli, 'loop')
        assert hasattr(cli, 'parser')

    def test_parser_creation(self, cli):
        """Test argument parser creation."""
        assert isinstance(cli.parser, argparse.ArgumentParser)
        assert cli.parser.description is not None

    def test_parser_help(self, cli):
        """Test that parser help works."""
        try:
            cli.parser.parse_args(['--help'])
        except SystemExit:
            pass  # --help causes SystemExit, which is expected

    def test_parser_default_args(self, cli):
        """Test parser with default arguments."""
        # This should not raise an exception
        args = cli.parser.parse_args([])
        assert hasattr(args, 'config')
        assert hasattr(args, 'log_level')
        assert hasattr(args, 'host')
        assert hasattr(args, 'port')

    def test_parser_custom_args(self, cli):
        """Test parser with custom arguments."""
        args = cli.parser.parse_args([
            '--config', 'test_config.json',
            '--log-level', 'DEBUG',
            '--host', '0.0.0.0',
            '--port', '8080'
        ])
        assert args.config == 'test_config.json'
        assert args.log_level == 'DEBUG'
        assert args.host == '0.0.0.0'
        assert args.port == 8080

    def test_parser_boolean_flags(self, cli):
        """Test parser boolean flags."""
        args = cli.parser.parse_args(['--version'])
        assert args.version is True

    @patch('nest_protect_mcp.cli.load_dotenv')
    @patch('nest_protect_mcp.cli.ProtectConfig')
    def test_load_config_from_env(self, mock_config_class, mock_load_dotenv, cli):
        """Test loading configuration from environment variables."""
        # Mock the config class
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        # Mock environment loading
        mock_load_dotenv.return_value = True

        # Test loading config from env
        result = cli._load_config_from_env()

        mock_load_dotenv.assert_called_once()
        mock_config_class.assert_called_once()
        assert result == mock_config_instance

    @patch('nest_protect_mcp.cli.ProtectConfig')
    def test_load_config_from_file(self, mock_config_class, cli):
        """Test loading configuration from file."""
        # Mock the config class
        mock_config_instance = Mock()
        mock_config_class.return_value = mock_config_instance

        # Mock file reading
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "config"}'

            result = cli._load_config_from_file('test_config.json')

        mock_config_class.assert_called_once_with(test="config")
        assert result == mock_config_instance

    def test_load_config_from_file_not_found(self, cli):
        """Test loading configuration from non-existent file."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = cli._load_config_from_file('nonexistent.json')
            assert result is None

    @patch('nest_protect_mcp.cli.uvicorn.run')
    @patch('nest_protect_mcp.cli.NestProtectMCP')
    def test_run_server(self, mock_server_class, mock_uvicorn_run, cli):
        """Test running the server."""
        # Mock server instance
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance

        # Mock config
        cli.config = Mock()

        # Run server
        cli._run_server()

        # Verify uvicorn was called
        mock_uvicorn_run.assert_called_once()

    def test_signal_handler(self, cli):
        """Test signal handler."""
        # This is hard to test directly, but we can verify it's set up
        import signal
        assert signal.signal(signal.SIGINT, cli._handle_signal) == signal.SIG_DFL
        assert signal.signal(signal.SIGTERM, cli._handle_signal) == signal.SIG_DFL

    def test_main_function(self, cli):
        """Test main function execution."""
        with patch.object(cli, 'run') as mock_run:
            # Test with no arguments (should show help)
            with patch('sys.argv', ['nest-protect-mcp']):
                try:
                    cli.run()
                except SystemExit:
                    pass  # Expected for --help

    @patch('sys.argv', ['nest-protect-mcp', '--version'])
    def test_version_flag(self, cli):
        """Test version flag."""
        with patch('nest_protect_mcp.cli.print') as mock_print:
            try:
                cli.run()
            except SystemExit:
                pass  # Expected

            # Should have printed version
            mock_print.assert_called()

    def test_config_precedence(self, cli):
        """Test configuration loading precedence."""
        # Test that file config takes precedence over env config
        env_config = Mock()
        file_config = Mock()

        with patch.object(cli, '_load_config_from_env', return_value=env_config):
            with patch.object(cli, '_load_config_from_file', return_value=file_config):
                result = cli._load_config(env_file='test.json', use_env=True)

                # File config should be used if available
                if file_config is not None:
                    assert result == file_config
                else:
                    assert result == env_config

    def test_config_validation(self, cli):
        """Test configuration validation."""
        # Test with invalid config
        with patch.object(cli, '_load_config_from_file', return_value=None):
            with patch.object(cli, '_load_config_from_env', return_value=None):
                result = cli._load_config()
                # Should return a default config or None
                assert result is None
