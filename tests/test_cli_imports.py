"""Basic test to verify CLI imports correctly."""

import unittest

from click.testing import CliRunner


class TestCLIImports(unittest.TestCase):
    """Test that the CLI can be imported and run without errors."""

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
            runner = CliRunner()
            # Run with --help to avoid actually connecting to AWS
            result = runner.invoke(main, ["--help"])
            self.assertEqual(result.exit_code, 0, f"CLI failed to run: {result.output}")
            self.assertIn("Usage:", result.output)
        except Exception as e:
            self.fail(f"Failed to run CLI: {str(e)}")