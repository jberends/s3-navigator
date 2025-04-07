"""Tests for the Navigator module."""

import unittest
from unittest import mock

from s3_navigator.navigator import S3Navigator


class TestS3Navigator(unittest.TestCase):
    """Test cases for the S3Navigator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the S3Client and Display
        self.mock_s3_client_patcher = mock.patch("s3_navigator.navigator.S3Client")
        self.mock_s3_client = self.mock_s3_client_patcher.start()
        self.mock_s3_client_instance = mock.MagicMock()
        self.mock_s3_client.return_value = self.mock_s3_client_instance

        self.mock_display_patcher = mock.patch("s3_navigator.navigator.Display")
        self.mock_display = self.mock_display_patcher.start()
        self.mock_display_instance = mock.MagicMock()
        self.mock_display.return_value = self.mock_display_instance

        # Create navigator instance
        self.navigator = S3Navigator(profile="test-profile", region="test-region")

    def tearDown(self):
        """Clean up after tests."""
        self.mock_s3_client_patcher.stop()
        self.mock_display_patcher.stop()

    def test_init(self):
        """Test initialization of navigator."""
        self.assertEqual(self.navigator.profile, "test-profile")
        self.assertEqual(self.navigator.region, "test-region")
        self.assertEqual(self.navigator.current_path, [])
        self.assertEqual(self.navigator.selected_items, [])
        self.assertEqual(self.navigator.sort_by, "name")
        self.assertFalse(self.navigator.sort_reverse)

    def test_list_buckets(self):
        """Test listing buckets."""
        # Setup mock return value for list_buckets
        mock_buckets = [
            {
                "name": "bucket1",
                "type": "BUCKET",
                "size": 0,
                "last_modified": "2023-01-01",
            },
            {
                "name": "bucket2",
                "type": "BUCKET",
                "size": 0,
                "last_modified": "2023-01-02",
            },
        ]
        self.mock_s3_client_instance.list_buckets.return_value = mock_buckets

        # Call the method
        self.navigator._list_buckets()

        # Verify results
        self.mock_s3_client_instance.list_buckets.assert_called_once()
        self.assertEqual(self.navigator.current_items, mock_buckets)
        self.assertEqual(self.navigator.current_path, [])
        self.mock_display_instance.update_view.assert_called_once_with(
            mock_buckets, [], []
        )

    def test_list_objects(self):
        """Test listing objects in a bucket."""
        # Setup test data
        self.navigator.current_path = ["test-bucket", "test-prefix"]

        # Setup mock return value for list_objects
        mock_objects = [
            {"name": "..", "type": "DIR", "size": 0, "last_modified": "2023-01-01"},
            {
                "name": "file1.txt",
                "type": "FILE",
                "size": 100,
                "last_modified": "2023-01-02",
            },
            {
                "name": "folder1",
                "type": "DIR",
                "size": 200,
                "last_modified": "2023-01-03",
            },
        ]
        self.mock_s3_client_instance.list_objects.return_value = mock_objects

        # Call the method
        self.navigator._list_objects()

        # Verify results
        self.mock_s3_client_instance.list_objects.assert_called_once_with(
            "test-bucket", "test-prefix/"
        )
        self.assertEqual(self.navigator.current_items, mock_objects)
        self.mock_display_instance.update_view.assert_called_once_with(
            mock_objects, ["test-bucket", "test-prefix"], []
        )

    def test_navigate_into(self):
        """Test navigating into a directory."""
        # Setup test data
        self.navigator.current_items = [
            {
                "name": "bucket1",
                "type": "BUCKET",
                "size": 0,
                "last_modified": "2023-01-01",
            },
            {
                "name": "bucket2",
                "type": "BUCKET",
                "size": 0,
                "last_modified": "2023-01-02",
            },
        ]
        self.mock_display_instance.selected_index = 0

        # Setup mock for _list_objects
        self.navigator._list_objects = mock.MagicMock()

        # Call the method
        self.navigator._navigate_into(0)

        # Verify results
        self.assertEqual(self.navigator.current_path, ["bucket1"])
        self.navigator._list_objects.assert_called_once()

    def test_navigate_up(self):
        """Test navigating up a directory level."""
        # Setup test data
        self.navigator.current_path = ["test-bucket", "test-prefix"]

        # Setup mocks
        self.navigator._list_objects = mock.MagicMock()
        self.navigator._list_buckets = mock.MagicMock()

        # Call the method
        self.navigator._navigate_up()

        # Verify results - should remove last path component
        self.assertEqual(self.navigator.current_path, ["test-bucket"])
        self.navigator._list_objects.assert_called_once()
        self.navigator._list_buckets.assert_not_called()

        # Test navigating up to root
        self.navigator.current_path = ["test-bucket"]
        self.navigator._list_objects.reset_mock()
        self.navigator._navigate_up()

        # Verify results - should be at root now
        self.assertEqual(self.navigator.current_path, [])
        self.navigator._list_buckets.assert_called_once()
        self.navigator._list_objects.assert_not_called()

    def test_toggle_selection(self):
        """Test toggling an item's selection."""
        # Setup test data
        self.navigator.current_items = [
            {
                "name": "file1.txt",
                "type": "FILE",
                "size": 100,
                "last_modified": "2023-01-01",
            },
            {
                "name": "file2.txt",
                "type": "FILE",
                "size": 200,
                "last_modified": "2023-01-02",
            },
        ]
        self.navigator.current_path = ["test-bucket"]
        self.mock_display_instance.selected_index = 0

        # Call the method to select an item
        self.navigator._handle_item_selection(0)

        # Verify results
        self.assertEqual(self.navigator.selected_items, ["test-bucket/file1.txt"])
        self.mock_display_instance.update_view.assert_called_with(
            self.navigator.current_items, ["test-bucket"], ["test-bucket/file1.txt"]
        )

        # Call again to deselect
        self.navigator._handle_item_selection(0)

        # Verify deselection
        self.assertEqual(self.navigator.selected_items, [])

    def test_delete_selected(self):
        """Test deleting selected items."""
        # Setup test data
        self.navigator.selected_items = [
            "test-bucket/file1.txt",
            "test-bucket/folder1/",
        ]
        self.mock_display_instance.confirm_deletion.return_value = True

        # Call the method
        self.navigator._delete_selected()

        # Verify results
        self.mock_display_instance.confirm_deletion.assert_called_once_with(
            ["test-bucket/file1.txt", "test-bucket/folder1/"]
        )
        self.assertEqual(self.mock_s3_client_instance.delete_object.call_count, 2)
        self.mock_s3_client_instance.delete_object.assert_any_call(
            "test-bucket", "file1.txt"
        )
        self.mock_s3_client_instance.delete_object.assert_any_call(
            "test-bucket", "folder1/"
        )
        self.assertEqual(self.navigator.selected_items, [])

    def test_refresh(self):
        """Test refreshing the current view."""
        # Setup mocks
        self.navigator._list_objects = mock.MagicMock()
        self.navigator._list_buckets = mock.MagicMock()

        # Test refresh at root level
        self.navigator.current_path = []
        self.navigator._refresh()
        self.navigator._list_buckets.assert_called_once()
        self.navigator._list_objects.assert_not_called()

        # Test refresh in a bucket/folder
        self.navigator.current_path = ["test-bucket"]
        self.navigator._list_buckets.reset_mock()
        self.navigator._refresh()
        self.navigator._list_objects.assert_called_once()
        self.navigator._list_buckets.assert_not_called()

    def test_toggle_sort(self):
        """Test toggling sort options."""
        # Initial state
        self.assertEqual(self.navigator.sort_by, "name")
        self.assertFalse(self.navigator.sort_reverse)

        # Mock methods
        self.navigator._sort_items = mock.MagicMock()
        self.navigator.display.update_view = mock.MagicMock()

        # First toggle: name -> size
        self.navigator._toggle_sort()
        self.assertEqual(self.navigator.sort_by, "size")
        self.assertFalse(self.navigator.sort_reverse)

        # Second toggle: size -> last_modified
        self.navigator._toggle_sort()
        self.assertEqual(self.navigator.sort_by, "last_modified")
        self.assertFalse(self.navigator.sort_reverse)

        # Third toggle: last_modified -> name with reverse
        self.navigator._toggle_sort()
        self.assertEqual(self.navigator.sort_by, "name")
        self.assertTrue(self.navigator.sort_reverse)

        # Verify sort_items and display update were called each time
        self.assertEqual(self.navigator._sort_items.call_count, 3)
        self.assertEqual(self.navigator.display.update_view.call_count, 3)

    def test_sort_items(self):
        """Test sorting items by different criteria."""
        # Setup test data
        self.navigator.current_items = [
            {
                "name": "b.txt",
                "type": "FILE",
                "size": 100,
                "last_modified": "2023-01-03",
            },
            {
                "name": "a.txt",
                "type": "FILE",
                "size": 300,
                "last_modified": "2023-01-01",
            },
            {
                "name": "c.txt",
                "type": "FILE",
                "size": 200,
                "last_modified": "2023-01-02",
            },
        ]

        # Test sort by name
        self.navigator.sort_by = "name"
        self.navigator.sort_reverse = False
        self.navigator._sort_items()
        sorted_names = [item["name"] for item in self.navigator.current_items]
        self.assertEqual(sorted_names, ["a.txt", "b.txt", "c.txt"])

        # Test sort by size
        self.navigator.sort_by = "size"
        self.navigator._sort_items()
        sorted_sizes = [item["size"] for item in self.navigator.current_items]
        self.assertEqual(sorted_sizes, [100, 200, 300])

        # Test sort by name reverse
        self.navigator.sort_by = "name"
        self.navigator.sort_reverse = True
        self.navigator._sort_items()
        sorted_names = [item["name"] for item in self.navigator.current_items]
        self.assertEqual(sorted_names, ["c.txt", "b.txt", "a.txt"])
