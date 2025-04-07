"""Tests for the CLI module."""

import unittest
from unittest import mock
from unittest.mock import MagicMock

from click.testing import CliRunner

from s3_navigator.cli import main


class TestCLI(unittest.TestCase):
    """Test cases for the CLI module."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @mock.patch("s3_navigator.cli.S3Navigator")
    def test_cli_default_options(self, mock_navigator: MagicMock):
        """Test CLI with default options."""
        # Setup mock
        mock_instance = mock.MagicMock()
        mock_navigator.return_value = mock_instance

        # Run command
        result = self.runner.invoke(main, [])

        # Verify results
        self.assertEqual(result.exit_code, 0)
        mock_navigator.assert_called_once_with(profile=None, region="eu-central-1")
        mock_instance.run.assert_called_once()

    @mock.patch("s3_navigator.cli.S3Navigator")
    def test_cli_with_options(self, mock_navigator: MagicMock):
        """Test CLI with custom options."""
        # Setup mock
        mock_instance = mock.MagicMock()
        mock_navigator.return_value = mock_instance

        # Run command with options
        result = self.runner.invoke(
            main, ["--profile", "test-profile", "--region", "us-west-2"]
        )

        # Verify results
        self.assertEqual(result.exit_code, 0)
        mock_navigator.assert_called_once_with(
            profile="test-profile", region="us-west-2"
        )
        mock_instance.run.assert_called_once()

    @mock.patch("s3_navigator.cli.S3Navigator")
    def test_cli_with_error(self, mock_navigator: MagicMock):
        """Test CLI handling errors."""
        # Setup mock to raise exception
        mock_instance = mock.MagicMock()
        mock_instance.run.side_effect = Exception("Test error")
        mock_navigator.return_value = mock_instance

        # Run command
        result = self.runner.invoke(main, [])

        # Verify results - should exit with error code
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Test error", result.output)
