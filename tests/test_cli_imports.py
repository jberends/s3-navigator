"""Basic test to verify CLI imports correctly and handles errors."""

import unittest
from unittest import mock

from click.testing import CliRunner


class TestCLIImports(unittest.TestCase):
    """Test that the CLI can be imported and run without errors."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_importable(self) -> None:
        """Test that the CLI module can be imported without errors."""
        try:
            from s3_navigator.cli import main
            assert callable(main), "CLI main function should be callable"
        except ImportError as e:
            self.fail(f"Failed to import CLI module: {str(e)}")

    def test_cli_runnable(self) -> None:
        """Test that the CLI can be run without import errors."""
        try:
            from s3_navigator.cli import main
            # Run with --help to avoid actually connecting to AWS
            result = self.runner.invoke(main, ["--help"])
            self.assertEqual(result.exit_code, 0, f"CLI failed to run: {result.output}")
            self.assertIn("Usage:", result.output)
        except Exception as e:
            self.fail(f"Failed to run CLI: {str(e)}")
            
    @mock.patch("s3_navigator.cli.S3Navigator")
    def test_cli_with_options(self, mock_navigator) -> None:
        """Test CLI with profile, region and serve options."""
        from s3_navigator.cli import main
        
        # Setup mock
        mock_instance = mock.MagicMock()
        mock_navigator.return_value = mock_instance
        
        # Run command with options
        result = self.runner.invoke(
            main, ["--profile", "test-profile", "--region", "us-west-2", "--serve"]
        )
        
        # Verify results
        self.assertEqual(result.exit_code, 0)
        mock_navigator.assert_called_once_with(
            profile="test-profile", region="us-west-2", serve=True
        )
        mock_instance.run.assert_called_once()
        
    @mock.patch("s3_navigator.cli.S3Navigator")
    def test_cli_error_handling(self, mock_navigator) -> None:
        """Test CLI handles exceptions properly."""
        from s3_navigator.cli import main
        
        # Setup mock
        mock_instance = mock.MagicMock()
        mock_instance.run.side_effect = Exception("Test error")
        mock_navigator.return_value = mock_instance
        
        # Run command
        result = self.runner.invoke(main, [])
        
        # Verify error handling
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error: Test error", result.output)
        
    @mock.patch("s3_navigator.cli.S3Navigator")
    def test_cli_keyboard_interrupt(self, mock_navigator) -> None:
        """Test CLI handles KeyboardInterrupt gracefully."""
        from s3_navigator.cli import main
        
        # Setup mock
        mock_instance = mock.MagicMock()
        mock_instance.run.side_effect = KeyboardInterrupt()
        mock_navigator.return_value = mock_instance
        
        # Run command
        result = self.runner.invoke(main, [])
        
        # Verify graceful exit
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Exiting S3 Navigator", result.output)