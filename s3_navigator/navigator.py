"""Core navigator class that handles S3 browsing functionality."""

from typing import Any, Dict, List, Optional

from s3_navigator.s3_client import S3Client
from s3_navigator.ui.display import Display, S3NavigatorDisplay


class S3Navigator:
    """Main class for navigating S3 buckets and objects."""

    def __init__(
        self,
        profile: Optional[str] = None,
        region: str = "eu-central-1",
        serve: bool = False,
    ):
        """Initialize the S3 Navigator.

        Args:
            profile: AWS profile name to use for authentication
            region: AWS region to use
            serve: If True, run in textual serve mode (web browser)
        """
        self.profile = profile
        self.region = region
        self.serve = serve
        self.s3_client = S3Client(profile=profile, region=region)
        self.display = Display()
        self.current_path: List[str] = []  # [bucket, prefix1, prefix2, ...]
        self.selected_items: List[str] = []  # List of selected item keys
        self.current_items: List[Dict[str, Any]] = []  # Current items being displayed
        self.sort_by = "name"  # Default sort by name
        self.sort_reverse = False

    def run(self) -> None:
        """Run the navigator interface."""
        # Get Access Key ID for display
        access_key_display = self.s3_client.access_key_id
        if access_key_display and len(access_key_display) > 10: # Truncate if too long
            access_key_display = f"...{access_key_display[-10:]}"
        elif not access_key_display:
            access_key_display = "Unknown"
            
        app_name = f"S3 Navigator - Profile: {self.profile or 'default'} (Region: {self.region}, KeyID: {access_key_display})"

        # Create a standalone Textual app directly
        app = S3NavigatorDisplay(
            name=app_name,
            profile=self.profile,
            region=self.region,
            access_key_id=self.s3_client.access_key_id # Pass the full key here for potential other uses
        )
        
        # Set up callbacks directly on the app
        app.path_changed_callback = self._handle_path_change
        app.item_selected_callback = self._handle_item_selection
        app.delete_callback = self._delete_selected
        app.refresh_callback = self._refresh
        app.sort_callback = self._toggle_sort
        
        # Get initial data
        self._list_buckets()
        
        # Initialize the app with the current data
        app.current_items = self.current_items
        app.current_path = self.current_path
        app.selected_items = self.selected_items
        
        # Run the app
        if self.serve:
            app.run()
        else:
            app.run()

    def _handle_path_change(self, direction: str, item_name: Optional[str]) -> None:
        """Handle path navigation from Textual UI.

        Args:
            direction: 'in' to navigate into a directory, 'up' to navigate up
            item_name: Name of the item to navigate into if direction is 'in'
        """
        if direction == "up":
            self._navigate_up()
        elif direction == "in" and item_name:
            # Find the item in current_items
            item_idx = next(
                (
                    i
                    for i, item in enumerate(self.current_items)
                    if item["name"] == item_name
                ),
                None,
            )
            if item_idx is not None:
                self._navigate_into(item_idx)

    def _handle_item_selection(self, idx: int) -> None:
        """Handle item selection from Textual UI.

        Args:
            idx: Index of the selected item
        """
        if 0 <= idx < len(self.current_items):
            item = self.current_items[idx]
            item_key = f"{'/'.join(self.current_path)}/{item['name']}".strip("/")

            if item_key in self.selected_items:
                self.selected_items.remove(item_key)
            else:
                self.selected_items.append(item_key)

            self.display.update_view(
                self.current_items, self.current_path, self.selected_items
            )

    def _list_buckets(self) -> None:
        """List all available S3 buckets."""
        self.current_path = []
        buckets_or_error = self.s3_client.list_buckets()

        if buckets_or_error and buckets_or_error[0].get("type") == "ERROR":
            # Handle the error case
            self.current_items = buckets_or_error # This will be the error dict list
        else:
            # Proceed as normal
            self.current_items = buckets_or_error
            self._sort_items() # Only sort if not an error
            
        self.display.update_view(
            self.current_items, self.current_path, self.selected_items
        )

    def _list_objects(self) -> None:
        """List objects in the current path."""
        if not self.current_path:  # At root level
            self._list_buckets()
            return

        bucket = self.current_path[0]
        prefix = "/".join(self.current_path[1:]) + (
            "/" if len(self.current_path) > 1 else ""
        )

        objects_or_error = self.s3_client.list_objects(bucket, prefix)

        if objects_or_error and objects_or_error[0].get("type") == "ERROR":
            self.current_items = objects_or_error # Pass error to display
        else:
            self.current_items = objects_or_error
            self._sort_items() # Only sort if not an error
            
        self.display.update_view(
            self.current_items, self.current_path, self.selected_items
        )

    def _navigate_into(self, selected_idx: int) -> None:
        """Navigate into the selected item.

        Args:
            selected_idx: Index of the selected item
        """
        if selected_idx < 0 or selected_idx >= len(self.current_items):
            return

        item = self.current_items[selected_idx]
        if item["type"] == "BUCKET" or item["type"] == "DIR":
            # Navigate into bucket or directory
            self.current_path.append(item["name"])
            self._list_objects()
        # Files can't be navigated into

    def _navigate_up(self) -> None:
        """Navigate up one level."""
        if not self.current_path:  # Already at root
            return

        self.current_path.pop()
        if not self.current_path:  # Back to bucket list
            self._list_buckets()
        else:  # Inside a bucket
            self._list_objects()

    def _delete_selected(self) -> None:
        """Delete selected items."""
        if not self.selected_items:
            return

        # Ask for confirmation
        if not self.display.confirm_deletion(self.selected_items):
            return

        for item_key in self.selected_items:
            parts = item_key.split("/")
            bucket = parts[0]
            key = "/".join(parts[1:]) if len(parts) > 1 else ""

            try:
                self.s3_client.delete_object(bucket, key)
            except Exception as e:
                self.display.show_error(f"Failed to delete {item_key}: {str(e)}")

        self.selected_items = []
        self._refresh()

    def _refresh(self) -> None:
        """Refresh the current view."""
        if not self.current_path:  # At root level
            self._list_buckets()
        else:  # Inside a bucket
            self._list_objects()

    def _toggle_sort(self) -> None:
        """Toggle sort method."""
        # Cycle through sort options
        sort_options = ["name", "size", "last_modified"]
        current_index = sort_options.index(self.sort_by)

        # If last option, move to first option and flip direction
        if current_index == len(sort_options) - 1:
            self.sort_by = sort_options[0]
            self.sort_reverse = not self.sort_reverse
        else:
            # Move to next sort option
            self.sort_by = sort_options[current_index + 1]

        self._sort_items()
        self.display.update_view(
            self.current_items, self.current_path, self.selected_items
        )

    def _sort_items(self) -> None:
        """Sort the current items based on sort criteria."""

        def get_sort_key(item: Dict[str, Any]) -> Any:
            if self.sort_by == "name":
                return item["name"].lower()
            elif self.sort_by == "size":
                return item.get("size", 0)
            elif self.sort_by == "last_modified":
                return item.get("last_modified", "")
            return item["name"].lower()

        self.current_items.sort(key=get_sort_key, reverse=self.sort_reverse)
