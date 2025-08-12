"""Writer for Retrosheet event files."""

from pathlib import Path
from typing import List

from .models import EventFile, Game, Play, Player


class RetrosheetWriter:
    """Writer for Retrosheet event files."""

    def write_event_file(self, event_file: EventFile, output_path: Path) -> None:
        """Write an event file to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for game in event_file.games:
                self._write_game(f, game)

    def _write_game(self, f, game: Game) -> None:
        """Write a single game to the file."""
        # Write game ID
        f.write(f"id,{game.game_id}\n")

        # Write version
        f.write("version,1\n")

        # Write info records
        if game.info.info_lines:
            # Prefer verbatim original info lines to preserve unknown keys and order
            for key, value in game.info.info_lines:
                # Only quote if value contains comma or spaces? Retrosheet allows unquoted; keep original format simple
                f.write(f'info,{key},"{value}"\n')
        else:
            # Fallback to structured fields
            if game.info.away_team:
                f.write(f'info,visteam,"{game.info.away_team}"\n')
            if game.info.home_team:
                f.write(f'info,hometeam,"{game.info.home_team}"\n')
            if game.info.date:
                f.write(f'info,date,"{game.info.date}"\n')
            if game.info.temperature:
                f.write(f'info,temp,"{game.info.temperature}"\n')
            if game.info.attendance:
                f.write(f'info,attendance,"{game.info.attendance}"\n')

            # Write umpire info
            for i, umpire in enumerate(game.info.umpires):
                if i == 0:
                    f.write(f'info,umphome,"{umpire}"\n')
                elif i == 1:
                    f.write(f'info,ump1b,"{umpire}"\n')
                elif i == 2:
                    f.write(f'info,ump2b,"{umpire}"\n')
                elif i == 3:
                    f.write(f'info,ump3b,"{umpire}"\n')

        # Write start records
        for player in game.players:
            f.write(
                f'start,{player.player_id},"{player.name}",{player.team},{player.batting_order},{player.fielding_position}\n'
            )

        # Write play records
        for play in game.plays:
            # If the original file had unknown count ("??") but the play was edited AND concluded
            # (has a play_description), write the calculated/current count. Otherwise, preserve original.
            if (
                play.original_count == "??"
                and play.edited
                and bool(play.play_description)
            ):
                count_to_write = play.count
            else:
                count_to_write = (
                    play.original_count
                    if play.original_count is not None
                    else play.count
                )
            f.write(
                f"play,{play.inning},{play.team},{play.batter_id},{count_to_write},{play.pitches},{play.play_description}\n"
            )

        # Write comments
        for comment in game.comments:
            f.write(f'com,"{comment}"\n')


def write_event_file(event_file: EventFile, output_path: Path) -> None:
    """Convenience function to write an event file."""
    writer = RetrosheetWriter()
    writer.write_event_file(event_file, output_path)
