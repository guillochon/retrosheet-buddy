"""Tests for automatic walk and strikeout functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_auto_walk(tmp_path):
    """Test automatic walk functionality."""
    # Create test game with a play that will reach 4 balls
    test_game = Game(
        game_id="TEST001",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="TEST1",
                count="00",
                pitches="",
                play_description="",
            ),
            Play(
                inning=1,
                team=0,
                batter_id="TEST2",
                count="00",
                pitches="",
                play_description="",
            ),
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Add 4 balls to trigger automatic walk
    for i in range(4):
        editor._add_pitch("B")

    # Check if automatic walk was triggered
    assert (
        current_play.play_description == "W"
    ), f"Expected W, got {current_play.play_description}"
    # With display capping, the count should show 3 balls and current strikes
    assert current_play.count == "30", f"Expected 30, got {current_play.count}"

    # Auto-advance still occurs on walk
    assert editor.current_play_index == 1


def test_auto_strikeout(tmp_path):
    """Test automatic strikeout functionality."""
    # Create test game with a play that will reach 3 strikes
    test_game = Game(
        game_id="TEST002",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="TEST1",
                count="00",
                pitches="",
                play_description="",
            ),
            Play(
                inning=1,
                team=0,
                batter_id="TEST2",
                count="00",
                pitches="",
                play_description="",
            ),
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Add 3 strikes to trigger automatic strikeout
    for i in range(3):
        editor._add_pitch("S")

    # Check if automatic strikeout was triggered
    assert (
        current_play.play_description == "K"
    ), f"Expected K, got {current_play.play_description}"
    assert current_play.count == "02", f"Expected 02, got {current_play.count}"

    # No auto-advance on strikeout anymore
    assert editor.current_play_index == 0


def test_auto_strikeout_with_swinging(tmp_path):
    """Test automatic strikeout with swinging strike."""
    # Create test game with a play that will reach 3 strikes
    test_game = Game(
        game_id="TEST003",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="TEST1",
                count="00",
                pitches="",
                play_description="",
            ),
            Play(
                inning=1,
                team=0,
                batter_id="TEST2",
                count="00",
                pitches="",
                play_description="",
            ),
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Add 2 called strikes and 1 swinging strike
    editor._add_pitch("C")  # Called strike
    editor._add_pitch("C")  # Called strike
    editor._add_pitch("S")  # Swinging strike

    # Check if automatic strikeout was triggered
    assert (
        current_play.play_description == "K"
    ), f"Expected K, got {current_play.play_description}"
    assert current_play.count == "02", f"Expected 02, got {current_play.count}"

    # No auto-advance on strikeout anymore
    assert editor.current_play_index == 0
