"""Command-line interface for S3 Navigator."""

import click
import json # For pretty printing the output

from s3_navigator.navigator import S3Navigator
from s3_navigator.s3_client import S3Client # Import S3Client


@click.command()
@click.option(
    "--profile", default=None, help="AWS profile name to use for authentication."
)
@click.option(
    "--region", default="eu-central-1", help="AWS region to use. Default: eu-central-1"
)
@click.option(
    "--serve", is_flag=True, default=False, help="Run in textual serve mode (web browser)"
)
@click.option(
    "--list-buckets", 
    is_flag=True, 
    default=False, 
    help="List available buckets and exit. Bypasses the TUI."
)
def main(profile: str, region: str, serve: bool, list_buckets: bool) -> None:
    """Launch the S3 Navigator interface or list buckets if specified."""
    
    if list_buckets:
        s3_client = S3Client(profile=profile, region=region)
        click.echo(f"Attempting to list buckets with profile='{profile or 'default'}', region='{region}'...")
        buckets_info = s3_client.list_buckets()
        click.echo(json.dumps(buckets_info, indent=2, default=str)) # Use default=str for datetime objects
        return # Exit after listing buckets

    navigator = S3Navigator(profile=profile, region=region, serve=serve)
    try:
        # Use the built-in run method which handles setup and initialization
        navigator.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        click.echo("Exiting S3 Navigator...")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
