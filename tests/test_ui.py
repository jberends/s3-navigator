"""Basic tests for the UI components."""

import unittest
from unittest import mock

from s3_navigator.ui.display import Display, S3NavigatorDisplay


class TestDisplay(unittest.TestCase):
    """Test cases for the Display class."""

    def test_init(self) -> None:
        """Test initialization of the Display."""
        display = Display()
        self.assertIsNone(display.app)
        self.assertEqual(display.selected_index, 0)
        self.assertEqual(display.path, [])
        self.assertEqual(display.items, [])
        self.assertEqual(display.selected_items, [])

    def test_update_view_without_app(self) -> None:
        """Test updating the view when no app is set."""
        display = Display()
        
        # Set up test data
        items = [
            {"name": "item1", "type": "BUCKET", "size": 0, "last_modified": "2023-01-01"},
            {"name": "item2", "type": "DIR", "size": 1024, "last_modified": "2023-01-02"},
            {"name": "item3", "type": "FILE", "size": 2048, "last_modified": "2023-01-03"},
        ]
        path = ["bucket", "folder"]
        selected = ["bucket/folder/item3"]
        
        # Call the method
        display.update_view(items, path, selected)
        
        # Verify the data was stored
        self.assertEqual(display.items, items)
        self.assertEqual(display.path, path)
        self.assertEqual(display.selected_items, selected)

    def test_update_view_with_app(self) -> None:
        """Test updating the view when app is set."""
        display = Display()
        display.app = mock.MagicMock()
        
        # Set up test data
        items = [
            {"name": "item1", "type": "BUCKET", "size": 0, "last_modified": "2023-01-01"},
        ]
        path = ["bucket"]
        selected = []
        
        # Call the method
        display.update_view(items, path, selected)
        
        # Verify the app's update_display method was called
        display.app.update_display.assert_called_once_with(items, path, selected)

    def test_confirm_deletion_without_app(self) -> None:
        """Test confirm deletion when no app is set."""
        display = Display()
        
        # Call the method with some items
        items = ["bucket/item1", "bucket/item2"]
        result = display.confirm_deletion(items)
        
        # Without an app, it should return False
        self.assertFalse(result)

    def test_confirm_deletion_with_app(self) -> None:
        """Test confirm deletion when app is set."""
        display = Display()
        display.app = mock.MagicMock()
        display.app.confirm_deletion.return_value = True
        
        # Call the method with some items
        items = ["bucket/item1", "bucket/item2"]
        result = display.confirm_deletion(items)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify the app's confirm_deletion method was called
        display.app.confirm_deletion.assert_called_once_with(items)


# We'll skip direct testing of S3NavigatorDisplay since it inherits from Textual's App
# which is challenging to instantiate in unit tests due to its complex initialization