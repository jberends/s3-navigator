"""Command-line interface for S3 Navigator."""

import click

from s3_navigator.navigator import S3Navigator


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
def main(profile: str, region: str, serve: bool) -> None:
    """Launch the S3 Navigator interface."""
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
