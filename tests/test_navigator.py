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
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["name"], "A")
        self.assertEqual(self.navigator.current_items[1]["name"], "M")
        self.assertEqual(self.navigator.current_items[2]["name"], "Z")
        
        # Test sort by size
        self.navigator.sort_by = "size"
        self.navigator._sort_items()
        self.assertEqual(self.navigator.current_items[0]["size"], 500)
        self.assertEqual(self.navigator.current_items[1]["size"], 1000)
        self.assertEqual(self.navigator.current_items[2]["size"], 2000)
        
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