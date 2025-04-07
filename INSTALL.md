# S3 Navigator Installation Guide

## Prerequisites

- Python 3.9 or newer
- uv or uvx package manager

## Installation Options

### 1. Install with uv

```bash
# Create a virtual environment (optional but recommended)
uv venv

# Activate the virtual environment
source .venv/bin/activate  # Unix/MacOS
.venv\Scripts\activate     # Windows

# Install S3 Navigator
uv pip install s3-navigator
```

### 2. Install with uvx

```bash
# Install directly with uvx
uvx pip install s3-navigator
```

### 3. Install from source (for development)

```bash
# Clone the repository
git clone https://github.com/yourusername/s3-navigator.git
cd s3-navigator

# Create a virtual environment and install in development mode
uv venv
source .venv/bin/activate  # Unix/MacOS
uv pip install -e ".[dev]"
```

## AWS Configuration

S3 Navigator uses boto3 for AWS authentication. Make sure you have AWS credentials configured:

1. Create an AWS credentials file at `~/.aws/credentials` with your access keys:
   ```
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY
   ```

2. Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
   export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
   export AWS_DEFAULT_REGION=eu-central-1
   ```

## Running S3 Navigator

After installation, simply run:

```bash
# Run with default profile and region
s3-navigator

# Run with a specific profile
s3-navigator --profile my-aws-profile

# Run with a specific region
s3-navigator --region us-west-2
```