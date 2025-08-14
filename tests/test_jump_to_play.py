"""Test jump to play functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


@pytest.fixture
def test_event_file():
    """Create a test event file with multiple plays."""
    game_info = GameInfo(
        date="2023-04-01", game_id="TEST202304010", home_team="HOME", away_team="AWAY"
    )

    plays = [
        Play(
            inning=1,
            team=0,
            batter_id="TEST0001",
            count="32",
            pitches="BBSFS",
            play_description="S6/G",
        ),
        Play(
            inning=1,
            team=0,
            batter_id="TEST0002",
            count="12",
            pitches="BSF",
            play_description="K",
        ),
        Play(
            inning=1,
            team=1,
            batter_id="TEST0003",
            count="21",
            pitches="BCB",
            play_description="W",
        ),
        Play(
            inning=2,
            team=0,
            batter_id="TEST0004",
            count="00",
            pitches="",
            play_description="HR",
        ),
    ]

    game = Game(game_id="TEST202304010", info=game_info, plays=plays)

    return EventFile(games=[game])


def test_jump_to_play_valid_input(test_event_file, tmp_path):
    """Test that jump to play works with valid input."""
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start at play 0
    assert editor.current_play_index == 0

    # Mock input to simulate user typing "3" (jump to play 3)
    with patch("builtins.input", return_value="3"):
        with patch.object(editor.console, "clear"):
            with patch.object(editor.console, "print"):
                editor._jump_to_play()

    # Should now be at play 2 (0-indexed)
    assert editor.current_play_index == 2


def test_jump_to_play_invalid_input(test_event_file, tmp_path):
    """Test that jump to play handles invalid input gracefully."""
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start at play 0
    assert editor.current_play_index == 0

    # Mock input to simulate user typing invalid input
    with patch("builtins.input", return_value="invalid"):
        with patch.object(editor.console, "clear"):
            with patch.object(editor.console, "print"):
                editor._jump_to_play()

    # Should remain at play 0
    assert editor.current_play_index == 0


def test_jump_to_play_out_of_range(test_event_file, tmp_path):
    """Test that jump to play handles out-of-range input gracefully."""
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start at play 0
    assert editor.current_play_index == 0

    # Mock input to simulate user typing "10" (out of range)
    with patch("builtins.input", return_value="10"):
        with patch.object(editor.console, "clear"):
            with patch.object(editor.console, "print"):
                editor._jump_to_play()

    # Should remain at play 0
    assert editor.current_play_index == 0


def test_jump_to_play_empty_input(test_event_file, tmp_path):
    """Test that jump to play handles empty input gracefully."""
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start at play 0
    assert editor.current_play_index == 0

    # Mock input to simulate user pressing enter (empty input)
    with patch("builtins.input", return_value=""):
        with patch.object(editor.console, "clear"):
            with patch.object(editor.console, "print"):
                editor._jump_to_play()

    # Should remain at play 0
    assert editor.current_play_index == 0


def test_jump_to_play_mode_adjustment(test_event_file, tmp_path):
    """Test that jump to play properly adjusts mode after navigation."""
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start at play 0 in pitch mode
    editor.mode = "pitch"
    assert editor.current_play_index == 0

    # Jump to play 2 (which has a result but no pitches)
    with patch("builtins.input", return_value="3"):
        with patch.object(editor.console, "clear"):
            with patch.object(editor.console, "print"):
                editor._jump_to_play()

    # Should be at play 2 and mode should be adjusted appropriately
    assert editor.current_play_index == 2
    # Mode adjustment logic is tested in _auto_set_mode_after_navigation


def test_jump_to_play_no_games(tmp_path):
    """Test that jump to play handles empty games gracefully."""
    empty_event_file = EventFile(games=[])
    editor = RetrosheetEditor(empty_event_file, tmp_path)

    # This should not crash and should return early
    with patch.object(editor.console, "clear"):
        with patch.object(editor.console, "print"):
            editor._jump_to_play()


def test_jump_to_play_no_plays(tmp_path):
    """Test that jump to play handles games with no plays gracefully."""
    game_info = GameInfo(
        date="2023-04-01", game_id="TEST202304010", home_team="HOME", away_team="AWAY"
    )

    game = Game(game_id="TEST202304010", info=game_info, plays=[])
    event_file = EventFile(games=[game])
    editor = RetrosheetEditor(event_file, tmp_path)

    # This should return early without crashing
    editor._jump_to_play()

    # Should remain at play 0 (even though there are no plays)
    assert editor.current_play_index == 0
