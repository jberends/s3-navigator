"""Tests for the UI components."""

import unittest
from datetime import datetime
from unittest import mock

from s3_navigator.ui.display import Display, S3NavigatorDisplay


class TestDisplay(unittest.TestCase):
    """Test cases for the Display class."""

    def setUp(self):
        """Set up test fixtures."""
        self.display = Display()
        self.display.app = mock.MagicMock()

    def test_update_view(self):
        """Test update_view method."""
        items = [
            {
                "name": "file1.txt",
                "type": "FILE",
                "size": 100,
                "last_modified": datetime.now(),
            }
        ]
        path = ["bucket1"]
        selected_items = ["bucket1/file1.txt"]

        self.display.update_view(items, path, selected_items)

        # Check that display state is updated
        self.assertEqual(self.display.items, items)
        self.assertEqual(self.display.path, path)
        self.assertEqual(self.display.selected_items, selected_items)

        # Check that app update_display is called
        self.display.app.update_display.assert_called_once_with(
            items, path, selected_items
        )

    def test_confirm_deletion(self):
        """Test confirm_deletion method."""
        items = ["bucket1/file1.txt", "bucket1/file2.txt"]

        # Set mock return value
        self.display.app.confirm_deletion.return_value = True

        # Call the method
        result = self.display.confirm_deletion(items)

        # Check results
        self.assertTrue(result)
        self.display.app.confirm_deletion.assert_called_once_with(items)

        # Test with app returning False
        self.display.app.confirm_deletion.return_value = False
        result = self.display.confirm_deletion(items)
        self.assertFalse(result)

    def test_show_error(self):
        """Test show_error method."""
        self.display.show_error("Test error message")
        # Nothing to verify since this is delegated to the Textual app


class TestS3NavigatorDisplay(unittest.TestCase):
    """Test cases for the S3NavigatorDisplay class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the callbacks
        self.mock_path_changed = mock.MagicMock()
        self.mock_item_selected = mock.MagicMock()
        self.mock_delete = mock.MagicMock()
        self.mock_refresh = mock.MagicMock()
        self.mock_sort = mock.MagicMock()

        # Patch textual app methods that we can't easily test
        self.patch_compose = mock.patch.object(S3NavigatorDisplay, "compose")
        self.mock_compose = self.patch_compose.start()
        self.mock_compose.return_value = []

        self.patch_on_mount = mock.patch.object(S3NavigatorDisplay, "on_mount")
        self.mock_on_mount = self.patch_on_mount.start()

        # Create app instance with mocked callbacks
        self.app = S3NavigatorDisplay(
            name="Test App",
            path_changed_callback=self.mock_path_changed,
            item_selected_callback=self.mock_item_selected,
            delete_callback=self.mock_delete,
            refresh_callback=self.mock_refresh,
            sort_callback=self.mock_sort,
        )

    def tearDown(self):
        """Clean up after tests."""
        self.patch_compose.stop()
        self.patch_on_mount.stop()

    def test_init(self):
        """Test initialization of display app."""
        self.assertEqual(self.app.name, "Test App")
        self.assertEqual(self.app.path_changed_callback, self.mock_path_changed)
        self.assertEqual(self.app.item_selected_callback, self.mock_item_selected)
        self.assertEqual(self.app.delete_callback, self.mock_delete)
        self.assertEqual(self.app.refresh_callback, self.mock_refresh)
        self.assertEqual(self.app.sort_callback, self.mock_sort)
        self.assertEqual(self.app.current_path, [])
        self.assertEqual(self.app.selected_items, [])
        self.assertEqual(self.app.current_items, [])

    @mock.patch("s3_navigator.ui.display.events.Key")
    def test_on_key(self, mock_key_event):
        """Test key event handling."""
        # Test quit key
        mock_key_event.key = "q"
        with mock.patch.object(self.app, "exit") as mock_exit:
            self.app.on_key(mock_key_event)
            mock_exit.assert_called_once()

        # Test refresh key
        mock_key_event.key = "r"
        self.app.on_key(mock_key_event)
        self.mock_refresh.assert_called_once()

        # Test sort key
        mock_key_event.key = "s"
        self.app.on_key(mock_key_event)
        self.mock_sort.assert_called_once()

        # Test delete key
        mock_key_event.key = "backspace"
        self.app.on_key(mock_key_event)
        self.mock_delete.assert_called_once()

    def test_update_display(self):
        """Test updating display content."""
        # Setup test data
        items = [
            {
                "name": "file1.txt",
                "type": "FILE",
                "size": 100,
                "last_modified": datetime.now(),
            },
            {
                "name": "folder1",
                "type": "DIR",
                "size": 0,
                "last_modified": datetime.now(),
            },
        ]
        path = ["bucket1"]
        selected_items = ["bucket1/file1.txt"]

        # Mock for query_one
        self.app.query_one = mock.MagicMock()
        mock_path_widget = mock.MagicMock()
        mock_table = mock.MagicMock()
        self.app.query_one.side_effect = lambda selector, cls: (
            mock_path_widget if selector == "#path_display" else mock_table
        )

        # Call the method
        self.app.update_display(items, path, selected_items)

        # Check that display state is updated
        self.assertEqual(self.app.current_items, items)
        self.assertEqual(self.app.current_path, path)
        self.assertEqual(self.app.selected_items, selected_items)

        # Check path widget was updated
        mock_path_widget.update.assert_called_once_with("Path: bucket1")

        # Check table was cleared
        mock_table.clear.assert_called_once()

        # Check rows were added (called twice for 2 items)
        self.assertEqual(mock_table.add_row.call_count, 2)

    def test_format_size(self):
        """Test size formatting."""
        test_cases = [
            (0, "0 B"),
            (1023, "1023.0 B"),
            (1024, "1.0 KB"),
            (1024 * 1024, "1.0 MB"),
            (1024 * 1024 * 1024, "1.0 GB"),
            (1024 * 1024 * 1024 * 1024, "1.0 TB"),
        ]

        for size, expected in test_cases:
            result = self.app._format_size(size)
            self.assertEqual(result, expected)

    def test_format_date(self):
        """Test date formatting."""
        test_date = datetime(2023, 5, 15, 14, 30)
        result = self.app._format_date(test_date)
        self.assertEqual(result, "2023-05-15 14:30")
