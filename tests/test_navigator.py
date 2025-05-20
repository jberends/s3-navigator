"""Basic tests for the S3Navigator class."""

import unittest
from unittest import mock
from typing import Any, Dict, List

from s3_navigator.navigator import S3Navigator


class TestS3Navigator(unittest.TestCase):
    """Test cases for the S3Navigator class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the S3Client and Display dependencies
        self.s3_client_patcher = mock.patch("s3_navigator.navigator.S3Client")
        self.display_patcher = mock.patch("s3_navigator.navigator.Display")
        
        # Start the patchers
        self.mock_s3_client_class = self.s3_client_patcher.start()
        self.mock_display_class = self.display_patcher.start()
        
        # Set up the mocks
        self.mock_s3_client = mock.MagicMock()
        self.mock_display = mock.MagicMock()
        
        # Make the mocked classes return the mocked instances
        self.mock_s3_client_class.return_value = self.mock_s3_client
        self.mock_display_class.return_value = self.mock_display
        
        # Create the navigator instance for testing
        self.navigator = S3Navigator(profile="test-profile", region="us-west-2")

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        # Stop the patchers
        self.s3_client_patcher.stop()
        self.display_patcher.stop()

    def test_init(self) -> None:
        """Test initialization of the navigator."""
        # Verify the navigator was initialized correctly
        self.assertEqual(self.navigator.profile, "test-profile")
        self.assertEqual(self.navigator.region, "us-west-2")
        self.assertEqual(self.navigator.serve, False)
        self.assertEqual(self.navigator.current_path, [])
        self.assertEqual(self.navigator.selected_items, [])
        self.assertEqual(self.navigator.current_items, [])
        self.assertEqual(self.navigator.sort_by, "name")
        self.assertEqual(self.navigator.sort_reverse, False)
        
        # Verify the S3Client was created with the correct parameters
        self.mock_s3_client_class.assert_called_once_with(
            profile="test-profile", region="us-west-2"
        )
        
        # Verify the Display was created
        self.mock_display_class.assert_called_once()

    def test_list_buckets(self) -> None:
        """Test listing buckets."""
        # Set up the mock to return some test buckets
        test_buckets = [
            {"name": "bucket1", "type": "BUCKET", "size": 0, "last_modified": "2023-01-01"},
            {"name": "bucket2", "type": "BUCKET", "size": 0, "last_modified": "2023-01-02"},
        ]
        self.mock_s3_client.list_buckets.return_value = test_buckets
        
        # Call the method
        self.navigator._list_buckets()
        
        # Verify the S3Client was called
        self.mock_s3_client.list_buckets.assert_called_once()
        
        # Verify the current items were updated
        self.assertEqual(self.navigator.current_items, test_buckets)
        
        # Verify the display was updated
        self.mock_display.update_view.assert_called_once_with(
            test_buckets, [], []
        )

    def test_sort_items(self) -> None:
        """Test sorting items by different criteria."""
        # Set up test data
        test_items = [
            {"name": "Z", "size": 1000, "last_modified": "2023-01-01"},
            {"name": "A", "size": 500, "last_modified": "2023-01-03"},
            {"name": "M", "size": 2000, "last_modified": "2023-01-02"},
        ]
        self.navigator.current_items = test_items.copy()
        
        # Test sort by name (default)
        self.navigator.sort_by = "name"
        self.navigator.sort_reverse = False
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["name"], "A")
        self.assertEqual(self.navigator.current_items[1]["name"], "M")
        self.assertEqual(self.navigator.current_items[2]["name"], "Z")

        # Test sort by name (reverse)
        self.navigator.sort_reverse = True
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["name"], "Z")
        self.assertEqual(self.navigator.current_items[1]["name"], "M")
        self.assertEqual(self.navigator.current_items[2]["name"], "A")
        self.navigator.sort_reverse = False # Reset for next tests
        
        # Test sort by size
        self.navigator.sort_by = "size"
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["size"], 500)
        self.assertEqual(self.navigator.current_items[1]["size"], 1000)
        self.assertEqual(self.navigator.current_items[2]["size"], 2000)

        # Test sort by size (reverse)
        self.navigator.sort_reverse = True
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["size"], 2000)
        self.assertEqual(self.navigator.current_items[1]["size"], 1000)
        self.assertEqual(self.navigator.current_items[2]["size"], 500)
        self.navigator.sort_reverse = False # Reset for next tests
        
        # Test sort by last_modified
        self.navigator.sort_by = "last_modified"
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["last_modified"], "2023-01-01")
        self.assertEqual(self.navigator.current_items[1]["last_modified"], "2023-01-02")
        self.assertEqual(self.navigator.current_items[2]["last_modified"], "2023-01-03")
        
        # Test reverse sort
        self.navigator.sort_reverse = True
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["last_modified"], "2023-01-03")
        self.assertEqual(self.navigator.current_items[1]["last_modified"], "2023-01-02")
        self.assertEqual(self.navigator.current_items[2]["last_modified"], "2023-01-01")

    def test_sort_items_mixed_types(self) -> None:
        """Test sorting items with mixed types (BUCKET, DIR, FILE)."""
        test_items_mixed = [
            {"name": "alpha.txt", "type": "FILE", "size": 100, "last_modified": "2023-01-01T10:00:00"},
            {"name": "my-bucket", "type": "BUCKET", "size": 0, "last_modified": "2023-01-03T12:00:00"}, # Buckets might have 0 size or no mod date
            {"name": "zeta-folder", "type": "DIR", "size": 0, "last_modified": "2023-01-02T11:00:00"}, # Dirs might have 0 size
            {"name": "beta.log", "type": "FILE", "size": 50, "last_modified": "2023-01-04T09:00:00"},
        ]
        self.navigator.current_items = test_items_mixed.copy()

        # Sort by name (ASC)
        self.navigator.sort_by = "name"
        self.navigator.sort_reverse = False
        self.navigator._sort_items()
        expected_names_asc = ["alpha.txt", "beta.log", "my-bucket", "zeta-folder"]
        self.assertEqual([item["name"] for item in self.navigator.current_items], expected_names_asc)

        # Sort by name (DESC)
        self.navigator.sort_reverse = True
        self.navigator._sort_items()
        expected_names_desc = ["zeta-folder", "my-bucket", "beta.log", "alpha.txt"]
        self.assertEqual([item["name"] for item in self.navigator.current_items], expected_names_desc)
        self.navigator.sort_reverse = False

        # Sort by size (ASC) - Relying on stable sort for items with the same size.
        self.navigator.sort_by = "size"
        self.navigator.sort_reverse = False
        self.navigator.current_items = test_items_mixed.copy() # Reset to original defined order
        self.navigator._sort_items()

        # Original order of items for stability reference:
        # alpha.txt (100), my-bucket (0), zeta-folder (0), beta.log (50)
        # Expected sorted order by size (ASC):
        # my-bucket (0) (appears before zeta-folder in original list)
        # zeta-folder (0)
        # beta.log (50)
        # alpha.txt (100)
        expected_size_asc_names = ["my-bucket", "zeta-folder", "beta.log", "alpha.txt"]
        self.assertEqual([item["name"] for item in self.navigator.current_items], expected_size_asc_names)

        # Sort by size (DESC)
        self.navigator.sort_by = "size"
        self.navigator.sort_reverse = True
        # self.navigator.current_items = test_items_mixed.copy() # Not needed if testing continuation from ASC
        self.navigator._sort_items()
        expected_size_desc_names = ["alpha.txt", "beta.log", "zeta-folder", "my-bucket"]
        self.assertEqual([item["name"] for item in self.navigator.current_items], expected_size_desc_names)
        self.navigator.sort_reverse = False

        # Sort by last_modified (ASC)
        self.navigator.sort_by = "last_modified"
        self.navigator._sort_items()
        expected_mod_asc = ["alpha.txt", "zeta-folder", "my-bucket", "beta.log"]
        self.assertEqual([item["name"] for item in self.navigator.current_items], expected_mod_asc)

        # Sort by last_modified (DESC)
        self.navigator.sort_reverse = True
        self.navigator._sort_items()
        expected_mod_desc = ["beta.log", "my-bucket", "zeta-folder", "alpha.txt"]
        self.assertEqual([item["name"] for item in self.navigator.current_items], expected_mod_desc)
        self.navigator.sort_reverse = False