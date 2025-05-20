"""Core navigator class that handles S3 browsing functionality."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from s3_navigator.s3_client import S3Client
from s3_navigator.ui.display import S3NavigatorDisplay


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
        self.app: Optional[S3NavigatorDisplay] = None
        self.current_path: List[str] = []
        self.selected_items: List[str] = []
        self.current_items: List[Dict[str, Any]] = []
        self.sort_by = "name"
        self.sort_reverse = False

    def log_to_display(self, message: str) -> None:
        """Log a message to the Textual display if available."""
        if self.app:
            self.app.add_log_message(message)

    def run(self) -> None:
        """Run the navigator interface."""
        self.log_to_display("Initializing S3 Navigator...")
        access_key_display = self.s3_client.access_key_id
        if access_key_display and len(access_key_display) > 10:
            access_key_display = f"...{access_key_display[-10:]}"
        elif not access_key_display:
            access_key_display = "Unknown"
            
        app_name = f"S3 Navigator - Profile: {self.profile or 'default'} (Region: {self.region}, KeyID: {access_key_display})"

        self.app = S3NavigatorDisplay(
            navigator_instance=self,
            name=app_name,
            profile=self.profile,
            region=self.region,
            access_key_id=self.s3_client.access_key_id
        )
        
        self.app.path_changed_callback = self._handle_path_change
        self.app.item_selected_callback = self._handle_item_selection
        self.app.delete_callback = self.request_delete_confirmation
        self.app.refresh_callback = self._refresh
        self.app.sort_callback = self._toggle_sort
        self.app.calculate_size_callback = self._handle_calculate_size_request
        self.app.calculate_all_sizes_callback = self._handle_calculate_all_sizes_request
        
        if self.serve:
            self.app.run()
        else:
            self.app.run()

    def _handle_path_change(self, direction: str, item_name: Optional[str]) -> None:
        """Handle path navigation from Textual UI.

        Args:
            direction: 'in' to navigate into a directory, 'up' to navigate up
            item_name: Name of the item to navigate into if direction is 'in'
        """
        if direction == "up":
            self._navigate_up()
        elif direction == "in" and item_name:
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
        if not self.app: return
        if 0 <= idx < len(self.current_items):
            item = self.current_items[idx]
            item_key = f"{'/'.join(self.current_path)}/{item['name']}".strip("/")

            if item_key in self.selected_items:
                self.selected_items.remove(item_key)
            else:
                self.selected_items.append(item_key)

            self.app.update_display(
                self.current_items, self.current_path, self.selected_items,
                self.sort_by, self.sort_reverse
            )

    def _list_buckets(self) -> None:
        """List all available S3 buckets."""
        if not self.app: return
        self.log_to_display("Listing buckets...")
        self.current_path = []
        buckets_or_error = self.s3_client.list_buckets()

        if buckets_or_error and buckets_or_error[0].get("type") == "ERROR":
            self.current_items = buckets_or_error
            self.log_to_display(f"Error listing buckets: {buckets_or_error[0].get('name')}")
        elif buckets_or_error and buckets_or_error[0].get("type") == "INFO":
            self.current_items = buckets_or_error
            self.log_to_display(f"Info listing buckets: {buckets_or_error[0].get('name')}")
        else:
            self.current_items = buckets_or_error
            self._sort_items()
            self.log_to_display(f"Found {len(self.current_items)} buckets.")
            
        self.app.update_display(
            self.current_items, self.current_path, self.selected_items,
            self.sort_by, self.sort_reverse
        )

    def _list_objects(self) -> None:
        """List objects in the current path."""
        if not self.app: return
        if not self.current_path:
            self.log_to_display("Current path is empty, listing buckets instead.")
            self._list_buckets()
            return

        bucket = self.current_path[0]
        prefix = "/".join(self.current_path[1:]) + (
            "/" if len(self.current_path) > 1 else ""
        )
        self.log_to_display(f"Listing objects in s3://{bucket}/{prefix}")

        objects_or_error = self.s3_client.list_objects(bucket, prefix)

        if objects_or_error and objects_or_error[0].get("type") == "ERROR":
            self.current_items = objects_or_error
            self.log_to_display(f"Error listing objects: {objects_or_error[0].get('name')}")
        elif objects_or_error and objects_or_error[0].get("type") == "INFO":
            self.current_items = objects_or_error
            self.log_to_display(f"Info listing objects: {objects_or_error[0].get('name')}")
        else:
            self.current_items = objects_or_error
            self._sort_items()
            self.log_to_display(f"Found {len(self.current_items)} items in s3://{bucket}/{prefix}")
            
        self.app.update_display(
            self.current_items, self.current_path, self.selected_items,
            self.sort_by, self.sort_reverse
        )

    def _navigate_into(self, selected_idx: int) -> None:
        """Navigate into the selected item.

        Args:
            selected_idx: Index of the selected item
        """
        if selected_idx < 0 or selected_idx >= len(self.current_items):
            return

        item = self.current_items[selected_idx]
        if item["name"] == "..":
            self._navigate_up()
        elif item["type"] == "BUCKET" or item["type"] == "DIR":
            self.log_to_display(f"Navigating into {item['type']}: {item['name']}")
            self.current_path.append(item["name"])
            self._list_objects()
        # Files can't be navigated into

    def _navigate_up(self) -> None:
        """Navigate up one level."""
        if not self.current_path:
            self.log_to_display("Already at root, cannot navigate up.")
            return

        self.log_to_display(f"Navigating up from: {'/'.join(self.current_path)}")
        self.current_path.pop()
        if not self.current_path:
            self.log_to_display("Navigated to root, listing buckets.")
            self._list_buckets()
        else:
            self._list_objects()

    def request_delete_confirmation(self) -> None:
        """Requests delete confirmation from the UI if items are selected."""
        if not self.app:
            return
        
        if not self.selected_items:
            self.log_to_display("No items selected to delete.")
            return
        
        # Collect all objects and total size for each selected item
        items_info = []
        for item_key in self.selected_items:
            parts = item_key.split("/")
            bucket = parts[0]
            key = "/".join(parts[1:]) if len(parts) > 1 else ""
            if key.endswith("/") or key == "":
                # Directory: collect all objects under prefix
                object_keys, total_size = self.s3_client.collect_objects_for_deletion(bucket, key)
                items_info.append({
                    "item_key": item_key,
                    "object_count": len(object_keys),
                    "total_size": total_size
                })
            else:
                # Single object
                obj = self.s3_client.get_object_metadata(bucket, key)
                items_info.append({
                    "item_key": item_key,
                    "object_count": 1,
                    "total_size": obj.get("Size", 0) if obj else 0
                })
        total_objects = sum(info["object_count"] for info in items_info)
        total_size = sum(info["total_size"] for info in items_info)
        
        self.log_to_display(f"Requesting UI confirmation to delete {total_objects} object(s), total size: {self.app._format_size(total_size) if self.app else total_size} ...")
        # The UI will call _execute_confirmed_delete if user confirms
        self.app.show_confirm_delete_dialog(list(self.selected_items), self._execute_confirmed_delete, total_objects, total_size)

    def _execute_confirmed_delete(self) -> None:
        """Execute deletion of selected items after UI confirmation."""
        if not self.app: 
            return # Should not happen if dialog was shown
        
        # Double check selected_items, though dialog implies they were there
        if not self.selected_items:
            self.log_to_display("Deletion confirmed, but no items are currently selected. Aborting.")
            return

        self.log_to_display(f"Deletion confirmed. Proceeding to delete selected items...")
        
        items_to_delete_copy = list(self.selected_items) 
        for item_key in items_to_delete_copy:
            parts = item_key.split("/")
            bucket = parts[0]
            key = "/".join(parts[1:]) if len(parts) > 1 else ""
            try:
                self.s3_client.delete_object(bucket, key, log_callback=self.log_to_display)
                self.log_to_display(f"Successfully deleted s3://{bucket}/{key}")
            except Exception as e:
                error_message = f"Delete Error: {item_key} - {str(e)}"
                self.log_to_display(error_message)
        self.selected_items = [] # Clear selection after attempting deletion
        self.log_to_display("Deletion process finished, refreshing view.")
        self._refresh()

    def _refresh(self) -> None:
        """Refresh the current view."""
        self.log_to_display(f"Refreshing view for: {'/'.join(self.current_path) or 'root'}")
        if not self.current_path:
            self._list_buckets()
        else:
            self._list_objects()

    def _toggle_sort(self) -> None:
        """Toggle sort method."""
        if not self.app: return
        self.log_to_display(f"Toggling sort. Current: {self.sort_by}, Reverse: {self.sort_reverse}")
        sort_options = ["name", "size", "last_modified"]
        current_index = sort_options.index(self.sort_by)

        if current_index == len(sort_options) - 1:
            self.sort_by = sort_options[0]
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = sort_options[current_index + 1]

        self._sort_items()
        self.log_to_display(f"Sort changed to: {self.sort_by}, Reverse: {self.sort_reverse}. Updating display.")
        self.app.update_display(
            self.current_items, self.current_path, self.selected_items,
            self.sort_by, self.sort_reverse
        )

    def _sort_items(self) -> None:
        """Sort the current items based on sort criteria."""
        def get_sort_key(item: Dict[str, Any]) -> Any:
            if self.sort_by == "name":
                return item["name"].lower()
            elif self.sort_by == "size":
                return item.get("size", 0)
            elif self.sort_by == "last_modified":
                dt = item.get("last_modified")
                if isinstance(dt, datetime):
                    # If aware, convert to naive UTC for comparison
                    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
                        return dt.astimezone(timezone.utc).replace(tzinfo=None)
                    return dt # Already naive
                return datetime.min # Fallback for non-datetime or missing values
            return item["name"].lower() # Default sort key if sort_by is unrecognized
        
        actual_items = [item for item in self.current_items if item.get("type") not in ("ERROR", "INFO")]
        error_info_items = [item for item in self.current_items if item.get("type") in ("ERROR", "INFO")]

        actual_items.sort(key=get_sort_key, reverse=self.sort_reverse)
        self.current_items = error_info_items + actual_items

    def _handle_calculate_size_request(self, item_name: str) -> None:
        """Handle request to calculate size for a specific item."""
        if not self.app:
            return

        target_item_index = -1
        for i, item_data in enumerate(self.current_items):
            if item_data.get("name") == item_name and item_data.get("type") in ["BUCKET", "DIR"]:
                target_item_index = i
                break
        
        if target_item_index == -1:
            self.log_to_display(f"Could not find item '{item_name}' to calculate size.")
            return

        item_to_calc = self.current_items[target_item_index]
        self.log_to_display(f"Calculating size for {item_to_calc['type']}: {item_to_calc['name']}...")

        bucket_name = ""
        object_prefix = ""

        if item_to_calc["type"] == "BUCKET":
            bucket_name = item_to_calc["name"]
            # For a bucket, the prefix for calculation is empty (all objects in bucket)
            object_prefix = "" 
            self.log_to_display(f"Target is BUCKET. Bucket: {bucket_name}, Prefix for S3: ''")
        elif item_to_calc["type"] == "DIR":
            if not self.current_path:
                # This shouldn't happen if a DIR is selected, as current_path should have the bucket.
                self.log_to_display(f"Error: DIR selected but current_path is empty.")
                return
            bucket_name = self.current_path[0]
            # Construct prefix: join current_path elements after bucket, then add item_name
            dir_path_parts = self.current_path[1:] + [item_to_calc["name"]]
            object_prefix = "/".join(dir_path_parts) + "/" # Ensure trailing slash for directories
            self.log_to_display(f"Target is DIR. Bucket: {bucket_name}, Current S3 Path: {'/'.join(self.current_path)}, Item: {item_to_calc['name']}. Prefix for S3: {object_prefix}")

        try:
            # Ensure s3_client has _calculate_directory_size method accessible
            calculated_size = self.s3_client._calculate_directory_size(bucket_name, object_prefix)
            self.current_items[target_item_index]["size"] = calculated_size
            self.log_to_display(f"Size calculation complete for {item_to_calc['name']}: {self.app._format_size(calculated_size) if self.app else calculated_size}")
        except Exception as e:
            self.log_to_display(f"Error calculating size for {item_to_calc['name']}: {e}")
            # Optionally set size back to -1 or an error indicator
            self.current_items[target_item_index]["size"] = -1 # Indicate error or keep pending

        # Refresh display
        if self.app:
            self.app.update_display(
                self.current_items,
                self.current_path,
                self.selected_items,
                self.sort_by,
                self.sort_reverse
            )

    def _handle_calculate_all_sizes_request(self) -> None:
        """Handle request to calculate size for all visible items with size -1."""
        if not self.app:
            return

        self.log_to_display("Starting batch size calculation for all visible pending items...") # Log 1 (from Navigator)
        
        items_to_process = [
            (i, item_data) for i, item_data in enumerate(self.current_items)
            if item_data.get("type") in ["BUCKET", "DIR"] and item_data.get("size") == -1
        ]
        
        if not items_to_process:
            self.log_to_display("No items found requiring size calculation.")
            return

        self.log_to_display(f"Found {len(items_to_process)} items to calculate. Scheduling loop...")
        
        # Schedule the actual loop to allow current log messages to render
        self.app.call_later(self._execute_batch_size_calculation_loop, items_to_process)

    def _execute_batch_size_calculation_loop(self, items_to_process: List[tuple[int, Dict[str, Any]]]) -> None:
        """Execute the loop for batch calculating directory/bucket sizes."""
        if not self.app: # Re-check app as this is called later
            print("Error: App context lost before executing batch size calculation loop.") # Or log if app still exists for logging
            return

        self.log_to_display(f"Executing batch calculation loop for {len(items_to_process)} items.")
        calculated_count = 0
        total_to_calculate = len(items_to_process)

        for i, item_data in items_to_process:
            # Ensure item_data is the dictionary, and i is its original index in self.current_items
            item_name = item_data["name"]
            item_type = item_data["type"]
            
            self.log_to_display(f"Processing {item_type}: {item_name} ({calculated_count + 1}/{total_to_calculate})...")
            
            bucket_name = ""
            object_prefix = ""

            if item_type == "BUCKET":
                bucket_name = item_name
                object_prefix = ""
            elif item_type == "DIR":
                if not self.current_path:
                    self.log_to_display(f"Error: DIR {item_name} found but current_path is empty. Skipping.")
                    continue
                bucket_name = self.current_path[0]
                dir_path_parts = self.current_path[1:] + [item_name]
                object_prefix = "/".join(dir_path_parts) + "/"
            
            try:
                calculated_size = self.s3_client._calculate_directory_size(bucket_name, object_prefix)
                # Update the original self.current_items list using the original index i
                if 0 <= i < len(self.current_items) and self.current_items[i]["name"] == item_name:
                    self.current_items[i]["size"] = calculated_size
                    self.log_to_display(f"Size for {item_name}: {self.app._format_size(calculated_size) if self.app else calculated_size}")
                else:
                    self.log_to_display(f"Error updating size for {item_name}: item not found at original index or name mismatch.")
                calculated_count += 1
            except Exception as e:
                self.log_to_display(f"Error calculating size for {item_name}: {e}")
                if 0 <= i < len(self.current_items) and self.current_items[i]["name"] == item_name:
                    self.current_items[i]["size"] = -1 # Keep as pending or mark error

            # Refresh display after each calculation to show progress if possible, though UI is blocked
            if self.app:
                self.app.update_display(
                    self.current_items,
                    self.current_path,
                    self.selected_items,
                    self.sort_by,
                    self.sort_reverse
                )
        
        self.log_to_display(f"Batch size calculation finished. Processed {calculated_count}/{total_to_calculate} items.")
        # Final refresh might be needed if any errors occurred and display wasn't updated for last item
        if self.app:
            self.app.update_display(
                self.current_items,
                self.current_path,
                self.selected_items,
                self.sort_by,
                self.sort_reverse
            )
