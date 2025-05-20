# S3 Navigator Specifications

## Overview
S3 Navigator is a command-line tool that provides a Norton Commander-style interface for browsing Amazon S3 buckets. The application allows users to navigate through S3 buckets and objects as if they were directories and files in a local file system.

## Core Requirements

### Functionality
- Browse S3 buckets and objects in a hierarchical, directory-like structure
- Display object metadata including size, creation time, and modification date
- Calculate and display directory sizes by summing all objects within a directory
- Support navigating up and down the directory tree
- Allow delete of objects or directories
- Sorting by name (default), size or modification date
- Provide real-time updates of current location in the tree
- Allow refreshing of directory content
- Maintain high performance even with large buckets

### User Interface
- Norton Commander-style interface with a clean, intuitive layout
- Color-coded display for different types of items (buckets, directories, files)
- Display a status bar with current location information
- Show help information for available commands
- Highlight the currently selected item
- provide a solid takeover of the terminal and perform very carefull redrawing of the screen
- A 6-line log window positioned above the footer, displaying log statements of backend calls.

### Input Handling
- Support keyboard navigation using arrow keys (up/down/right (directory down) and left (directory up))
- Spacebar for additional actions (select for an operation), allow multiple selections. 
- Support for macOS and unix type input handling
- 'BACKSPACE' or 'DELETE' to delete selected
- 'q' to quit the application
- 'r' to refresh the current view
- 's' to sort on name ASC, name DESC, size ASC, size DESC, modification time ASC/DESC
- 'C' to calculate sizes of all visible uncalculated items

### Performance Considerations
- Implement efficient caching to minimize API calls to AWS
- Optimize directory size calculations for large buckets
- Ensure responsive UI even when dealing with high latency
- Support pagination for buckets with many objects
- Implement lazy loading for directory contents

## Technical Specifications

### Dependencies
- **boto3**: AWS SDK for Python to interact with S3
- **click**: Command-line interface creation kit
- **textual**: Rich widget style command line application interface. Use most from this package - allow access via web through --server or --demon flag
- **rich**: Rich text and beautiful formatting in the terminal (optional)
- **yaspin**: Terminal spinners for loading indication
- **termcolor**: Colored terminal text (use `textual` predominantly)

### AWS Integration
- Use boto3 session and client for S3 interactions
- Support AWS profiles for authentication
- Default region set to eu-central-1
- Handle proper error messages for AWS API failures
- Support S3 object listing with pagination

### Data Structures
- Cache mechanisms for S3 object listings
- Directory size tracking across navigation
- Path handling for S3 key management
- Item representation with metadata

### Cross-Platform Support
- Unix-like systems (Linux, macOS) support using tty and termios and limited support for Windows
- Handle different key codes between operating systems
- Consistent terminal rendering across platforms

### Error Handling
- Graceful handling of AWS API errors
- Informative error messages for connection issues
- Recovery options when operations fail
- Fallback mechanisms for unsupported features

## User Commands

| Key | Function |
|-----|----------|
| ↑/↓ | Move selection up/down |
| right arrow /Enter | Open selected bucket/directory |
| left arrow | Navigate to parent directory |
| Space | add to selection / deselect |
| backspace | delete (with confirmation dialog) |
| q | Quit the application |
| r | Refresh current view |
| s | sort tree |
| c | Calculate size of selected directory/bucket |
| C | Calculate sizes of all visible uncalculated items |

## Implementation 

- create uv / uvx package
- allow upload to PyPI eventual
- ask me questions for the pyproject.toml file
- Author name: Jochem Berends
- add a github repo to is: https://github.com/jberends/s3-navigator.git
- checkout the main from the repo as it already contains README and gitignore and such
- update existing README.md file
- write tests where possible based on pytest
- use github actions to perform tests
- use github actions to release to PyPI, put instructions to provide the pypi TOKEN as environment variable to the action
- use github actions for dependency check

## Visual Design

### Main Interface Components
1. **Header**: Application title and AWS profile/region information
2. **Location Bar**: Breadcrumb of Current bucket and path
3. **Item Table**: List of buckets/directories/files with metadata
   - Name with appropriate emoji (🪣 bucket, 📁 folder, 📄 file)
   - Type (BUCKET, DIR, FILE)
   - Size (human-readable format: B, KB, MB, GB, TB)
   - Last modified timestamp
4. **Log Window**: A 6-line area above the footer to display backend activity logs.
5. **Help Panel**: Available keyboard commands

### Color Scheme
- norton commander style color scheme (see provided image for reference)

## Command-Line Options
- `--profile`: Specify AWS profile name to use
- `--region`: Specify AWS region (default: eu-central-1)
- `--serve`: run in textual -serve mode as a web inside the webbrowser

## Limitations
- No file content preview
- No file upload/download functionality
- No file modification capabilities
- Does not display bucket policies or permissions
- Limited search capabilities

## Future Enhancements
- File preview functionality.
- File previde of MD or JSON files using 'rich'.
- File upload/download functionality
- Search capabilities
- File/directory operations (copy, move, delete)
- Split-pane view for easier navigation between locations
- Bookmarks for frequently accessed locations
- Advanced filtering options
- Support for S3 bucket versioning
