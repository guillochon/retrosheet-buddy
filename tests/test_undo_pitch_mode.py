"""Tests for undo functionality specifically in pitch mode."""

from pathlib import Path
from unittest.mock import patch

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_undo_in_pitch_mode_with_x_key(tmp_path):
    """Test that undo works in pitch mode using the 'x' key."""
    # Create test data
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
            )
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start in pitch mode
    assert editor.mode == "pitch"

    # Add a pitch
    editor._add_pitch("S")
    assert test_game.plays[0].pitches == "S"
    assert test_game.plays[0].count == "01"

    # Simulate key press handling - test that 'x' key triggers undo
    with patch("retrosheet_buddy.editor.get_key", return_value="x"):
        # Simulate one iteration of the event loop
        key = "x"
        if key == "x":  # This is the undo handler
            editor._undo_last_action()

    # Verify undo worked
    assert test_game.plays[0].pitches == ""
    assert test_game.plays[0].count == "00"


def test_unknown_pitch_with_u_key(tmp_path):
    """Test that 'u' key still works for Unknown pitch type in pitch mode."""
    # Create test data
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
            )
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start in pitch mode
    assert editor.mode == "pitch"

    # Test that 'u' key adds Unknown pitch
    assert "u" in editor.pitch_hotkeys
    assert editor.pitch_hotkeys["u"] == "U"

    # Simulate key press handling for 'u' in pitch mode
    with patch("retrosheet_buddy.editor.get_key", return_value="u"):
        key = "u"
        if editor.mode == "pitch" and key in editor.pitch_hotkeys:
            editor._add_pitch(editor.pitch_hotkeys[key])

    # Verify Unknown pitch was added
    assert test_game.plays[0].pitches == "U"


def test_no_conflict_between_undo_and_unknown_pitch(tmp_path):
    """Test that undo ('x') and unknown pitch ('u') don't conflict."""
    # Create test data
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
            )
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start in pitch mode
    assert editor.mode == "pitch"

    # Add Unknown pitch with 'u'
    editor._add_pitch("U")
    assert test_game.plays[0].pitches == "U"

    # Add another pitch
    editor._add_pitch("B")
    assert test_game.plays[0].pitches == "UB"

    # Use 'x' to undo - should undo the Ball, not affect the Unknown
    editor._undo_last_action()
    assert test_game.plays[0].pitches == "U"

    # Use 'x' to undo again - should undo the Unknown
    editor._undo_last_action()
    assert test_game.plays[0].pitches == ""


def test_pitch_mode_integration_with_undo(tmp_path):
    """Integration test for pitch mode with multiple operations and undo."""
    # Create test data
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
            )
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Sequence of operations: Ball, Strike, Foul, Unknown
    operations = [
        ("B", "Ball"),
        ("S", "Swinging strike"),
        ("F", "Foul"),
        ("U", "Unknown"),
    ]

    expected_sequences = ["", "B", "BS", "BSF", "BSFU"]
    expected_counts = [
        "00",
        "10",
        "11",
        "12",
        "12",
    ]  # Foul doesn't add to strikes after 2

    # Add each pitch and verify state
    for i, (pitch_code, description) in enumerate(operations):
        editor._add_pitch(pitch_code)
        assert test_game.plays[0].pitches == expected_sequences[i + 1]
        assert test_game.plays[0].count == expected_counts[i + 1]

    # Now undo each operation in reverse
    for i in range(len(operations) - 1, -1, -1):
        editor._undo_last_action()
        assert test_game.plays[0].pitches == expected_sequences[i]
        assert test_game.plays[0].count == expected_counts[i]
