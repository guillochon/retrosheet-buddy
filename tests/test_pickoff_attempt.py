"""Tests for pickoff attempt functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_pitcher_pickoff_attempt_first_base(tmp_path):
    """Test that pitcher pickoff attempt to first base adds '1' to pitches."""
    # Create test game with a play
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

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Trigger pickoff attempt wizard
    editor._add_pitch("PK")

    # Should be in pickoff attempt wizard mode
    assert editor.pickoff_attempt_active
    assert editor.pickoff_attempt_player is None
    assert editor.pickoff_attempt_base is None

    # Select pitcher
    editor._handle_pickoff_attempt_input("p")
    assert editor.pickoff_attempt_player == "pitcher"
    assert editor.pickoff_attempt_base is None

    # Select first base
    editor._handle_pickoff_attempt_input("1")

    # Check that pickoff attempt was added and wizard was reset
    assert not editor.pickoff_attempt_active
    assert editor.pickoff_attempt_player is None
    assert editor.pickoff_attempt_base is None
    assert current_play.pitches == "1"
    assert current_play.count == "00"  # Pickoff doesn't change count


def test_catcher_pickoff_attempt_second_base(tmp_path):
    """Test that catcher pickoff attempt to second base adds '+2' to pitches."""
    # Create test game with a play
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
            )
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Trigger pickoff attempt wizard
    editor._add_pitch("PK")

    # Select catcher
    editor._handle_pickoff_attempt_input("c")
    assert editor.pickoff_attempt_player == "catcher"

    # Select second base
    editor._handle_pickoff_attempt_input("2")

    # Check that pickoff attempt was added with plus sign
    assert current_play.pitches == "+2"
    assert current_play.count == "00"  # Pickoff doesn't change count


def test_pickoff_attempt_after_existing_pitches(tmp_path):
    """Test that pickoff attempt is appended to existing pitches."""
    # Create test game with a play that already has pitches
    test_game = Game(
        game_id="TEST003",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="TEST1",
                count="11",
                pitches="BS",
                play_description="",
            )
        ],
    )

    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Trigger pickoff attempt wizard
    editor._add_pitch("PK")

    # Select pitcher and third base
    editor._handle_pickoff_attempt_input("p")
    editor._handle_pickoff_attempt_input("3")

    # Check that pickoff attempt was appended
    assert current_play.pitches == "BS3"
    assert (
        current_play.count == "11"
    )  # Count remains the same since pickoff doesn't affect it


def test_multiple_pickoff_attempts(tmp_path):
    """Test multiple pickoff attempts in sequence."""
    # Create test game with a play
    test_game = Game(
        game_id="TEST004",
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

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # First pickoff attempt - pitcher to first
    editor._add_pitch("PK")
    editor._handle_pickoff_attempt_input("p")
    editor._handle_pickoff_attempt_input("1")
    assert current_play.pitches == "1"

    # Second pickoff attempt - catcher to second
    editor._add_pitch("PK")
    editor._handle_pickoff_attempt_input("c")
    editor._handle_pickoff_attempt_input("2")
    assert current_play.pitches == "1+2"

    # Third pickoff attempt - pitcher to third
    editor._add_pitch("PK")
    editor._handle_pickoff_attempt_input("p")
    editor._handle_pickoff_attempt_input("3")
    assert current_play.pitches == "1+23"


def test_pickoff_attempt_mixed_with_regular_pitches(tmp_path):
    """Test pickoff attempts mixed with regular pitches."""
    # Create test game with a play
    test_game = Game(
        game_id="TEST005",
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

    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]

    # Regular pitch first
    editor._add_pitch("B")
    assert current_play.pitches == "B"
    assert current_play.count == "10"

    # Pickoff attempt - pitcher to first
    editor._add_pitch("PK")
    editor._handle_pickoff_attempt_input("p")
    editor._handle_pickoff_attempt_input("1")
    assert current_play.pitches == "B1"
    assert current_play.count == "10"  # Count unchanged by pickoff

    # Another regular pitch
    editor._add_pitch("S")
    assert current_play.pitches == "B1S"
    assert current_play.count == "11"

    # Another pickoff attempt - catcher to second
    editor._add_pitch("PK")
    editor._handle_pickoff_attempt_input("c")
    editor._handle_pickoff_attempt_input("2")
    assert current_play.pitches == "B1S+2"
    assert current_play.count == "11"  # Count unchanged by pickoff


def test_pickoff_attempt_wizard_state_reset_on_completion(tmp_path):
    """Test that wizard state is properly reset after completion."""
    # Create test game with a play
    test_game = Game(
        game_id="TEST006",
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

    # Start with first play
    editor.current_play_index = 0

    # Trigger pickoff attempt wizard
    editor._add_pitch("PK")
    assert editor.pickoff_attempt_active

    # Complete the wizard
    editor._handle_pickoff_attempt_input("p")
    editor._handle_pickoff_attempt_input("1")

    # Verify state is reset
    assert not editor.pickoff_attempt_active
    assert editor.pickoff_attempt_player is None
    assert editor.pickoff_attempt_base is None

    # Should be able to start a new pickoff attempt
    editor._add_pitch("PK")
    assert editor.pickoff_attempt_active
    assert editor.pickoff_attempt_player is None
    assert editor.pickoff_attempt_base is None
