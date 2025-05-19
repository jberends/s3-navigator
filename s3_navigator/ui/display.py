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

    current_path = reactive[List[str]]([])
    selected_items = reactive[List[str]]([])
    current_items = reactive[List[Dict[str, Any]]]([])

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "sort", "Sort"),
        ("space", "select", "Select"),
        ("backspace", "delete", "Delete"),
        ("right", "open", "Open"),
        ("left", "up", "Up"),
    ]

    def __init__(
        self,
        name: str = "S3 Navigator",
        profile: Optional[str] = None,
        region: Optional[str] = None,
        path_changed_callback: Optional[Callable] = None,
        item_selected_callback: Optional[Callable] = None,
        delete_callback: Optional[Callable] = None,
        refresh_callback: Optional[Callable] = None,
        sort_callback: Optional[Callable] = None,
    ):
        """Initialize the display.

        Args:
            name: Application name
            profile: AWS profile
            region: AWS region
            path_changed_callback: Callback for when path changes
            item_selected_callback: Callback for when item is selected
            delete_callback: Callback for deletion action
            refresh_callback: Callback for refresh action
            sort_callback: Callback for sort action
        """
        super().__init__()
        self.app_title = name  # Store name as an attribute
        self.profile = profile
        self.region = region
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
        self.title = self.app_title
        table = self.query_one("#item_table", DataTable)
        table.add_columns("Type", "Name", "Size", "Last Modified")

        # Update Footer with profile and region
        footer = self.query_one(Footer)
        footer_text = f"Profile: {self.profile or 'default'} | Region: {self.region or 'unknown'}"
        # Textual's Footer displays BINDINGS automatically.
        # To add custom text, we might need to make a custom Footer or add a Static widget.
        # For now, let's try to update the existing footer's renderable if possible,
        # or add a new Static widget to the footer.
        # A simpler approach for now, given the direct `highlight_key` was removed,
        # is to add a Static widget *above* the standard Footer for this info.
        # However, the Footer is typically for key bindings.
        # Let's check if Footer can have a custom renderable or if we should adjust the Header.
        # For simplicity, let's add this to the Header's title for now, as Footer is auto-populated.
        self.sub_title = footer_text

        from textual.screen import Screen
        if not self.screen_stack:
            class MainScreen(Screen):
                def compose(inner_self) -> ComposeResult:
                    yield from self.compose()
            self.push_screen(MainScreen())

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
            items: List of items to display, or an error dict
            path: Current path
            selected_items: List of selected item keys
        """
        self.current_items = items
        self.current_path = path
        self.selected_items = selected_items

        path_widget = self.query_one("#path_display", Static)
        table = self.query_one("#item_table", DataTable)
        table.clear()

        if items and items[0].get("type") == "ERROR":
            error_item = items[0]
            error_name = error_item.get("name", "Unknown Error")
            error_message = error_item.get("message", "An unexpected error occurred.")
            path_widget.update(f"Error: {error_name} - {error_message}")
            # Optionally, you could add a single row to the table with the error too
            # table.add_row("ERROR", error_name, error_message, "")
        else:
            # Update path display
            if path:
                path_str = "/".join(path)
                path_widget.update(f"Path: {path_str}")
            else:
                path_widget.update("Path: / (Buckets)") # Clarify when showing buckets

            # Update table
            for idx, item in enumerate(items):
                item_key = f"{{"/".join(path)}}/{item['name']}".strip("/")
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

    app: Optional[S3NavigatorDisplay]
    selected_index: int
    path: List[str]
    items: List[Dict[str, Any]]
    selected_items: List[str]

    def __init__(self, console: Any = None) -> None:
        """Initialize the display manager.

        Args:
            console: Rich console instance (not used, for compatibility)
        """
        self.console = console
        self.app = None
        self.selected_index = 0
        self.path = []
        self.items = []
        self.selected_items = []

    def setup(self) -> None:
        """Set up the terminal for display."""
        # Create app with appropriate callbacks
        self.app = S3NavigatorDisplay(
            name="S3 Navigator",
            profile=None,  # These will be set by the navigator
            region=None,
            path_changed_callback=None,
            item_selected_callback=None,
            delete_callback=None,
            refresh_callback=None,
            sort_callback=None,
        )
        
    def run(self) -> None:
        """Run the Textual app."""
        if self.app:
            # Update display with current data before running
            self.app.update_display(self.items, self.path, self.selected_items)
            
            # Create a simple import we can use to create a textual screen
            from textual.screen import Screen
            
            # Create a default screen and push it to the stack
            class MainScreen(Screen):
                def compose(self) -> ComposeResult:
                    # Re-yield the same widgets that are in the App.compose method
                    yield from self.app.compose()
            
            # Push the screen to the app's stack
            main_screen = MainScreen()
            self.app.push_screen(main_screen)
            
            # Now run the app
            self.app.run()

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
