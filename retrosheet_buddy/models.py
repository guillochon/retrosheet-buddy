"""Data models for Retrosheet event file records."""

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class GameInfo(BaseModel):
    """Information about a game from info records."""

    date: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    temperature: Optional[str] = None
    attendance: Optional[str] = None
    umpires: List[str] = Field(default_factory=list)
    # Preserve all info lines as (key, value) pairs in original order to avoid data loss
    info_lines: List[Tuple[str, str]] = Field(default_factory=list)


class Player(BaseModel):
    """Player information from start/sub records."""

    player_id: str
    name: str
    team: int  # 0 for visiting, 1 for home
    batting_order: int  # 1-9, 0 for DH
    fielding_position: int  # 1-9, 10 for DH, 11 for PH, 12 for PR


class Play(BaseModel):
    """A play record from the event file."""

    inning: int
    team: int  # 0 for visiting, 1 for home
    batter_id: str
    count: str  # e.g., "00", "12", "??"
    original_count: Optional[str] = None  # original count from file (preserves "??")
    pitches: str  # pitch sequence
    play_description: str  # the actual play result
    edited: bool = False  # True if the play has been edited in the editor


class Game(BaseModel):
    """Complete game data."""

    game_id: str
    info: GameInfo
    players: List[Player] = Field(default_factory=list)
    plays: List[Play] = Field(default_factory=list)
    comments: List[str] = Field(default_factory=list)


class EventFile(BaseModel):
    """Complete event file containing multiple games."""

    games: List[Game] = Field(default_factory=list)
