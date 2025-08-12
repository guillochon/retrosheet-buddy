"""Main CLI entry point for Retrosheet Buddy."""

import sys
from pathlib import Path
from typing import Optional

import click

from .editor import run_editor


@click.command()
@click.argument(
    "event_file", type=click.Path(exists=True, path_type=Path), required=False
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("outputs"),
    help="Output directory for edited files",
)
@click.option(
    "--game-id", "-g", help="Game ID to create new event file (not implemented yet)"
)
def main(event_file: Optional[Path], output_dir: Path, game_id: Optional[str]) -> None:
    """
    Interactive Retrosheet event file editor.

    EVENT_FILE: Path to existing Retrosheet event file (.EVN, .EVA, etc.)

    If no event file is provided, you can specify a game ID to create a new file
    (this feature is not yet implemented).
    """
    if not event_file and not game_id:
        click.echo("Error: Must provide either an event file or a game ID", err=True)
        sys.exit(1)

    if not event_file and game_id:
        click.echo(
            "Error: Creating new event files from game ID is not yet implemented",
            err=True,
        )
        sys.exit(1)

    if event_file:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"Loading event file: {event_file}")
        click.echo(f"Output directory: {output_dir}")
        click.echo("Starting interactive editor...")

        run_editor(event_file, output_dir)


if __name__ == "__main__":
    main()
