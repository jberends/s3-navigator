"""Display management for the S3 Navigator interface using Textual."""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static


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
    """

    current_path = reactive([])
    selected_items = reactive([])
    current_items = reactive([])

    def __init__(
        self,
        name: str = "S3 Navigator",
        path_changed_callback: Optional[Callable] = None,
        item_selected_callback: Optional[Callable] = None,
        delete_callback: Optional[Callable] = None,
        refresh_callback: Optional[Callable] = None,
        sort_callback: Optional[Callable] = None,
    ):
        """Initialize the display.

        Args:
            name: Application name
            path_changed_callback: Callback for when path changes
            item_selected_callback: Callback for when item is selected
            delete_callback: Callback for deletion action
            refresh_callback: Callback for refresh action
            sort_callback: Callback for sort action
        """
        super().__init__()
        self.name = name
        self.path_changed_callback = path_changed_callback
        self.item_selected_callback = item_selected_callback
        self.delete_callback = delete_callback
        self.refresh_callback = refresh_callback
        self.sort_callback = sort_callback

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Static("", classes="path", id="path_display")
        yield DataTable(id="item_table", classes="s3-table")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Set up data table
        table = self.query_one("#item_table", DataTable)
        table.add_columns("Type", "Name", "Size", "Last Modified")

        # Set up footer
        footer = self.query_one(Footer)
        footer.highlight_key("q", "Quit")
        footer.highlight_key("r", "Refresh")
        footer.highlight_key("s", "Sort")
        footer.highlight_key("space", "Select")
        footer.highlight_key("backspace", "Delete")
        footer.highlight_key("right", "Open")
        footer.highlight_key("left", "Up")

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

    def update_display(
        self, items: List[Dict[str, Any]], path: List[str], selected_items: List[str]
    ) -> None:
        """Update the display with new data.

        Args:
            items: List of items to display
            path: Current path
            selected_items: List of selected item keys
        """
        self.current_items = items
        self.current_path = path
        self.selected_items = selected_items

        # Update path display
        path_widget = self.query_one("#path_display", Static)
        if path:
            path_str = "/".join(path)
            path_widget.update(f"Path: {path_str}")
        else:
            path_widget.update("Path: /")

        # Update table
        table = self.query_one("#item_table", DataTable)
        table.clear()

        for idx, item in enumerate(items):
            item_key = f"{'/'.join(path)}/{item['name']}".strip("/")
            is_selected = item_key in selected_items

            # Set emoji based on type
            if item["type"] == "BUCKET":
                type_icon = "🪣"
            elif item["type"] == "DIR":
                type_icon = "📁"
            else:
                type_icon = "📄"

            # Format size
            size_str = self._format_size(item["size"])

            # Format last modified
            last_modified = self._format_date(item["last_modified"])

            # Add selection marker
            name_display = f"{'* ' if is_selected else '  '}{item['name']}"

            table.add_row(type_icon, name_display, size_str, last_modified)

    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
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


class Display:
    """Legacy display adapter to bridge between navigator and Textual app."""

    def __init__(self, console=None) -> None:
        """Initialize the display manager.

        Args:
            console: Rich console instance (not used, for compatibility)
        """
        self.app = None
        self.selected_index = 0
        self.path = []
        self.items = []
        self.selected_items = []

    def setup(self) -> None:
        """Set up the terminal for display."""
        pass  # Will be handled when we run the app

    def teardown(self) -> None:
        """Restore terminal settings."""
        pass  # Will be handled by the app

    def get_key(self) -> str:
        """Get a keypress from the user - not used with Textual."""
        # Not needed with Textual, but kept for compatibility
        return ""

    def update_view(
        self, items: List[Dict[str, Any]], path: List[str], selected_items: List[str]
    ) -> None:
        """Update the displayed view.

        Args:
            items: List of items to display
            path: Current path
            selected_items: List of selected item keys
        """
        self.items = items
        self.path = path
        self.selected_items = selected_items

        if self.app:
            self.app.update_display(items, path, selected_items)

    def move_selection(self, direction: int) -> None:
        """Move the current selection up or down.

        Args:
            direction: -1 for up, 1 for down
        """
        # This will be handled by Textual
        pass

    def confirm_deletion(self, items: List[str]) -> bool:
        """Show deletion confirmation dialog.

        Args:
            items: List of items to delete

        Returns:
            True if confirmed, False otherwise
        """
        if self.app:
            return self.app.confirm_deletion(items)
        return False

    def show_error(self, message: str) -> None:
        """Show an error message to the user.

        Args:
            message: Error message to display
        """
        # Would be better implemented with a Textual notification
        pass
