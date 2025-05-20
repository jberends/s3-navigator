"""Display management for the S3 Navigator interface using Textual."""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from textual import events
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static, Log

# Forward declaration for type hint
if TYPE_CHECKING:
    from s3_navigator.navigator import S3Navigator


class S3NavigatorDisplay(App):
    """Textual app for S3 Navigator."""

    CSS = """
    Screen {
        align: center middle;
    }
    
    Header {
        dock: top;
        background: $accent;
        color: $text;
    }
    
    Footer {
        dock: bottom;
        background: $accent;
        color: $text;
    }
    
    .path {
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    
    .s3-table {
        height: 1fr;
        border: round $accent;
    }

    #log_window {
        height: 6;
        border: round $primary;
        background: $panel;
        padding: 0 1;
        dock: bottom; /* Docks above the footer which also docks bottom */
    }
    """

    current_path = reactive[List[str]]([])
    selected_items = reactive[List[str]]([])
    current_items = reactive[List[Dict[str, Any]]]([])

    # Base column names
    BASE_COLUMNS = ["Type", "Name", "Size", "Last Modified"]
    SORTABLE_COLUMNS_MAP = {
        "name": "Name",
        "size": "Size",
        "last_modified": "Last Modified",
    }

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "sort", "Sort"),
        ("space", "select", "Select"),
        ("backspace", "delete", "Delete"),
        ("right", "open", "Open"),
        ("left", "up", "Up"),
        ("c", "calculate_size", "Calc. Size"),
        ("C", "calculate_all_sizes", "Calc. All Sizes"),
    ]

    def __init__(
        self,
        navigator_instance: Optional['S3Navigator'] = None,
        name: str = "S3 Navigator",
        profile: Optional[str] = None,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        path_changed_callback: Optional[Callable] = None,
        item_selected_callback: Optional[Callable] = None,
        delete_callback: Optional[Callable] = None,
        refresh_callback: Optional[Callable] = None,
        sort_callback: Optional[Callable] = None,
        calculate_size_callback: Optional[Callable] = None,
        calculate_all_sizes_callback: Optional[Callable] = None,
    ):
        """Initialize the display.

        Args:
            navigator_instance: Instance of S3Navigator
            name: Application name (can include profile, region, key ID)
            profile: AWS profile
            region: AWS region
            access_key_id: AWS Access Key ID
            path_changed_callback: Callback for when path changes
            item_selected_callback: Callback for when item is selected
            delete_callback: Callback for deletion action
            refresh_callback: Callback for refresh action
            sort_callback: Callback for sort action
            calculate_size_callback: Callback for calculate size action
            calculate_all_sizes_callback: Callback for calculate all sizes action
        """
        super().__init__()
        self.navigator_instance = navigator_instance
        self.app_title = name
        self.profile = profile
        self.region = region
        self.access_key_id = access_key_id
        self.path_changed_callback = path_changed_callback
        self.item_selected_callback = item_selected_callback
        self.delete_callback = delete_callback
        self.refresh_callback = refresh_callback
        self.sort_callback = sort_callback
        self.calculate_size_callback = calculate_size_callback
        self.calculate_all_sizes_callback = calculate_all_sizes_callback

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Static("", classes="path", id="path_display")
        yield DataTable(id="item_table", classes="s3-table")
        yield Log(id="log_window", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app on mount."""
        self.title = self.app_title
        table = self.query_one("#item_table", DataTable)
        # Use * operator to unpack the list of base column names
        table.add_columns(*self.BASE_COLUMNS)
        self.sub_title = f"Profile: {self.profile or 'default'} | Region: {self.region or 'unknown'}"

        # Load initial data by calling back to the navigator instance
        if self.navigator_instance:
            self.navigator_instance._list_buckets()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard input."""
        key = event.key

        if key == "q":
            self.exit()
        elif key == "r" and self.refresh_callback:
            self.refresh_callback()
        elif key == "s" and self.sort_callback:
            self.sort_callback()
        elif key == "backspace" and self.delete_callback:
            self.delete_callback()
        elif key == "space" and self.item_selected_callback:
            table = self.query_one("#item_table", DataTable)
            if table.cursor_row is not None:
                self.item_selected_callback(table.cursor_row)
        elif key == "right" or key == "enter":
            # Navigate into selected item
            table = self.query_one("#item_table", DataTable)
            if table.cursor_row is not None and self.path_changed_callback:
                item_idx = table.cursor_row
                if item_idx < len(self.current_items):
                    item = self.current_items[item_idx]
                    if item["type"] == "BUCKET" or item["type"] == "DIR":
                        self.path_changed_callback("in", item["name"])
        elif key == "left":
            # Navigate up one level
            if self.path_changed_callback:
                self.path_changed_callback("up", None)

    def action_calculate_size(self) -> None:
        """Action to trigger size calculation for the selected item."""
        table = self.query_one("#item_table", DataTable)
        if table.cursor_row is not None and self.calculate_size_callback:
            if 0 <= table.cursor_row < len(self.current_items):
                item = self.current_items[table.cursor_row]
                if item["type"] == "BUCKET" or item["type"] == "DIR":
                    self.add_log_message(f"Requesting size calculation for {item['type']}: {item['name']}...")
                    self.calculate_size_callback(item["name"]) 
                else:
                    self.add_log_message(f"Cannot calculate size for item type: {item['type']}.")
            else:
                self.add_log_message("No valid item selected for size calculation.")
        elif not self.calculate_size_callback:
            self.add_log_message("Size calculation callback not configured.")
        else:
            self.add_log_message("No item selected in the table.")

    def action_calculate_all_sizes(self) -> None:
        """Action to trigger size calculation for all visible pending items."""
        if self.calculate_all_sizes_callback:
            self.add_log_message("Requesting calculation for ALL visible pending item sizes...")
            self.calculate_all_sizes_callback()
        else:
            self.add_log_message("Calculate all sizes callback not configured.")

    def add_log_message(self, message: str) -> None:
        """Add a message to the log window."""
        log_widget = self.query_one("#log_window", Log)
        log_widget.write_line(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def update_display(
        self, 
        items: List[Dict[str, Any]], 
        path: List[str], 
        selected_items: List[str],
        sort_by: str,
        sort_reverse: bool
    ) -> None:
        """Update the display with new data.

        Args:
            items: List of items to display, or an error dict
            path: Current path
            selected_items: List of selected item keys
            sort_by: The field being sorted by
            sort_reverse: True if sort is descending, False otherwise
        """
        self.current_items = items
        self.current_path = path
        self.selected_items = selected_items

        path_widget = self.query_one("#path_display", Static)
        table = self.query_one("#item_table", DataTable)

        # Update column headers with sort indicators
        column_keys = list(table.columns.keys())
        new_labels = list(self.BASE_COLUMNS) # Start with base names

        for i, base_label in enumerate(self.BASE_COLUMNS):
            indicator = ""
            # Check if this base_label corresponds to the current sort_by field
            # This requires finding which sort_by key maps to the current base_label
            current_sort_field_display_name = self.SORTABLE_COLUMNS_MAP.get(sort_by)
            if current_sort_field_display_name == base_label:
                indicator = " \u25BC" if sort_reverse else " \u25B2" # ▼ or ▲
            new_labels[i] = f"{base_label}{indicator}"

        # Update the labels of existing columns
        # This assumes the order of columns in table.columns matches BASE_COLUMNS
        for col_key, new_label in zip(column_keys, new_labels):
            table.columns[col_key].label = new_label
        
        # Ensure the table refreshes its header (might be automatic with reactive labels)
        table.refresh(layout=True)

        table.clear()

        if items and items[0].get("type") == "ERROR":
            error_item = items[0]
            error_name = error_item.get("name", "Unknown Error")
            error_message = error_item.get("message", "An unexpected error occurred.")
            path_widget.update(f"{error_name}: {error_message}")
        elif items and items[0].get("type") == "INFO":
            info_item = items[0]
            info_name = info_item.get("name", "Information")
            info_message = info_item.get("message", "")
            path_widget.update(f"{info_name}: {info_message}")
        else:
            # Update path display
            if path:
                path_str = "/".join(path)
                path_widget.update(f"Path: {path_str}")
            else:
                path_widget.update("Path: / (Buckets)") # Clarify when showing buckets

            # Update table
            for idx, item in enumerate(items):
                # Construct item_key correctly
                if path: # If path is not empty, join it and add the item name
                    item_key = f"{''.join(path)}/{item['name']}"
                else: # If path is empty (listing buckets), item_key is just the bucket name
                    item_key = item['name']
                item_key = item_key.strip("/") # Ensure no leading/trailing slashes for consistency
                
                is_selected = item_key in selected_items

                if item["type"] == "BUCKET":
                    type_icon = "🪣"
                elif item["type"] == "DIR":
                    type_icon = "📁"
                else:
                    type_icon = "📄"

                size_str = self._format_size(item["size"])
                last_modified = self._format_date(item["last_modified"])
                name_display = f"{'* ' if is_selected else '  '}{item['name']}"

                table.add_row(type_icon, name_display, size_str, last_modified)

    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        if size_bytes == -1:
            return "[pending]"
        if size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    def _format_date(self, date: datetime) -> str:
        """Format date in a human-readable format.

        Args:
            date: Datetime object

        Returns:
            Formatted date string
        """
        return date.strftime("%Y-%m-%d %H:%M")

    def confirm_deletion(self, items: List[str]) -> bool:
        """Show deletion confirmation dialog.

        Args:
            items: List of items to delete

        Returns:
            True if confirmed, False otherwise
        """
        # In a real implementation, this would use a Textual modal dialog
        # For now, we'll just return True to simplify the example
        return True
