"""Writer for Retrosheet event files."""

from pathlib import Path

from .models import EventFile, Game


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

        # Build substitution index mapping: insertion index -> list of subs
        substitutions_by_index = {}
        for sub in getattr(game, "substitutions", []):
            substitutions_by_index.setdefault(sub.insertion_play_index, []).append(sub)

        # Write play records interleaving substitutions at recorded indices
        for play_index, play in enumerate(game.plays):
            # Write any substitutions that occurred before this play
            for sub in substitutions_by_index.get(play_index, []):
                f.write(
                    f'sub,{sub.player_id},"{sub.name}",{sub.team},{sub.batting_order},{sub.fielding_position}\n'
                )

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

        # Write any substitutions that occur after the final play
        for sub in substitutions_by_index.get(len(game.plays), []):
            f.write(
                f'sub,{sub.player_id},"{sub.name}",{sub.team},{sub.batting_order},{sub.fielding_position}\n'
            )

        # Write comments
        for comment in game.comments:
            f.write(f'com,"{comment}"\n')

        # Write data records (e.g., earned runs), preserve order
        for data_record in getattr(game, "data_records", []):
            if data_record.values:
                f.write(
                    "data,"
                    + data_record.record_type
                    + ","
                    + ",".join(data_record.values)
                    + "\n"
                )
            else:
                f.write("data," + data_record.record_type + "\n")


def write_event_file(event_file: EventFile, output_path: Path) -> None:
    """Convenience function to write an event file."""
    writer = RetrosheetWriter()
    writer.write_event_file(event_file, output_path)
