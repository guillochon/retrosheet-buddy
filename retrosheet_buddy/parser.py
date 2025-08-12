"""Parser for Retrosheet event files."""

import re
from pathlib import Path
from typing import List, Optional

from .models import EventFile, Game, GameInfo, Play, Player


class RetrosheetParser:
    """Parser for Retrosheet event files."""

    def __init__(self):
        self.current_game: Optional[Game] = None
        self.event_file = EventFile()

    def _calculate_count(self, pitches: str) -> str:
        """Calculate count from pitch sequence following baseball rules."""
        balls = 0
        strikes = 0

        for pitch in pitches:
            if pitch == "B":
                balls += 1
            elif pitch in ["S", "C"]:  # Swinging strike, Called strike
                strikes += 1
            elif pitch == "F":  # Foul ball
                # Foul balls only count as strikes up to 2 strikes
                if strikes < 2:
                    strikes += 1
            # Other pitch types (T, H, V, A, M, P, I, Q, R, E, N, O, U) don't affect count

        # Cap balls at 4 (walk) and strikes at 3 (strikeout)
        balls = min(balls, 4)
        strikes = min(strikes, 3)

        return f"{balls}{strikes}"

    def parse_file(self, file_path: Path) -> EventFile:
        """Parse a Retrosheet event file."""
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                self._parse_line(line)

        # Add the last game if there is one
        if self.current_game:
            self.event_file.games.append(self.current_game)

        return self.event_file

    def _parse_line(self, line: str) -> None:
        """Parse a single line from the event file."""
        if line.startswith("id,"):
            # Start of a new game
            if self.current_game:
                self.event_file.games.append(self.current_game)

            game_id = line.split(",")[1]
            self.current_game = Game(game_id=game_id, info=GameInfo())

        elif line.startswith("info,"):
            self._parse_info(line)

        elif line.startswith("start,"):
            self._parse_start(line)

        elif line.startswith("play,"):
            self._parse_play(line)

        elif line.startswith("com,"):
            self._parse_comment(line)

    def _parse_info(self, line: str) -> None:
        """Parse an info record."""
        if not self.current_game:
            return

        parts = line.split(",", 2)
        if len(parts) < 3:
            return

        info_type = parts[1]
        data = parts[2].strip('"')

        # Always append raw info key/value to preserve order and unknown fields
        self.current_game.info.info_lines.append((info_type, data))

        if info_type == "visteam":
            self.current_game.info.away_team = data
        elif info_type == "hometeam":
            self.current_game.info.home_team = data
        elif info_type == "date":
            self.current_game.info.date = data
        elif info_type == "temp":
            self.current_game.info.temperature = data
        elif info_type == "attendance":
            self.current_game.info.attendance = data
        elif info_type.startswith("umphome") or info_type.startswith("ump"):
            self.current_game.info.umpires.append(data)

    def _parse_start(self, line: str) -> None:
        """Parse a start record."""
        if not self.current_game:
            return

        parts = line.split(",")
        if len(parts) < 5:
            return

        player = Player(
            player_id=parts[1],
            name=parts[2].strip('"'),
            team=int(parts[3]),
            batting_order=int(parts[4]),
            fielding_position=int(parts[5]),
        )
        self.current_game.players.append(player)

    def _parse_play(self, line: str) -> None:
        """Parse a play record."""
        if not self.current_game:
            return

        parts = line.split(",")
        if len(parts) < 6:
            return

        # Preserve original count and calculate working count
        original_count = parts[4]
        pitches = parts[5]

        # Store original count and calculate working count for display/logic
        if original_count == "??":
            count = self._calculate_count(pitches)
        else:
            count = original_count

        play = Play(
            inning=int(parts[1]),
            team=int(parts[2]),
            batter_id=parts[3],
            count=count,
            original_count=original_count,
            pitches=pitches,
            play_description=parts[6],
            edited=False,
        )
        self.current_game.plays.append(play)

    def _parse_comment(self, line: str) -> None:
        """Parse a comment record."""
        if not self.current_game:
            return

        comment = line[4:].strip('"')  # Remove 'com,' and quotes
        self.current_game.comments.append(comment)


def parse_event_file(file_path: Path) -> EventFile:
    """Convenience function to parse an event file."""
    parser = RetrosheetParser()
    return parser.parse_file(file_path)
