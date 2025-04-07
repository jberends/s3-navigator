# S3 Navigator

A Norton Commander-style interface for browsing Amazon S3 buckets directly from your terminal.

## Features

- Browse S3 buckets and objects in a hierarchical, directory-like structure
- Display object metadata including size, creation time, and modification date
- Calculate and display directory sizes by summing all objects within a directory
- Support navigating up and down the directory tree
- Allow deletion of objects or directories
- Sorting by name (default), size, or modification date
- Supported on Unix-like systems (Linux, macOS) with limited Windows support

## Installation

```bash
# Install with uv
uv pip install s3-navigator

# Or install with uvx
uvx pip install s3-navigator
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Usage

```bash
# Run with default profile and region
s3-navigator

# Run with a specific profile
s3-navigator --profile myprofile

# Run with a specific region
s3-navigator --region us-west-2
```

## Controls

| Key | Function |
|-----|----------|
| ↑/↓ | Move selection up/down |
| →/Enter | Open selected bucket/directory |
| ← | Navigate to parent directory |
| Space | Add to selection / deselect |
| Backspace | Delete (with confirmation dialog) |
| q | Quit the application |
| r | Refresh current view |
| s | Sort tree |

## Development

```bash
# Clone the repository
git clone https://github.com/jberends/s3-navigator.git
cd s3-navigator

# Create environment and install in development mode
uv venv
source .venv/bin/activate  # Unix/macOS
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linting and type checking
uv run black --check .
uv run mypy s3_navigator
```

### Web Interface

Run S3 Navigator in a web browser using Textual's serve mode:

```bash
s3-navigator --serve
```

This opens a browser window with the S3 Navigator interface, which can be useful for remote operation or when you prefer a web interface.

## License

[MIT License](LICENSE)
