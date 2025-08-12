"""Tests for the detail mode functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_enter_detail_mode(tmp_path):
    """Test entering detail mode after selecting a play result."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Add a play to work with
    test_game = event_file.games[0]
    test_game.plays.append(
        Play(
            inning=1,
            team=0,
            batter_id="test0001",
            count="00",
            pitches="",
            play_description="",
        )
    )

    # Enter detail mode with a single
    editor._enter_detail_mode("S")

    assert editor.mode == "detail"
    assert editor.detail_mode_result == "S"
    assert editor.detail_mode_hit_type is None
    assert editor.detail_mode_fielding_position is None


def test_detail_mode_hit_type_selection(tmp_path):
    """Test selecting hit type in detail mode."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Enter detail mode
    editor._enter_detail_mode("S")

    # Select hit type
    editor._handle_detail_mode_input("g")  # Grounder
    assert editor.detail_mode_hit_type == "G"
    assert editor.detail_mode_fielding_position is None

    # Select different hit type
    editor._handle_detail_mode_input("l")  # Line drive
    assert editor.detail_mode_hit_type == "L"  # Should update


def test_detail_mode_fielding_position_selection(tmp_path):
    """Test selecting fielding position in detail mode."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Add a play to work with
    test_game = event_file.games[0]
    test_game.plays.append(
        Play(
            inning=1,
            team=0,
            batter_id="test0001",
            count="00",
            pitches="",
            play_description="",
        )
    )

    # Enter detail mode and select hit type
    editor._enter_detail_mode("S")
    editor._handle_detail_mode_input("g")  # Grounder

    # Select fielding position - this should automatically save and progress
    editor._handle_detail_mode_input("6")  # Shortstop

    # Verify that the play was saved and we're now in Hit Location builder within detail mode
    assert test_game.plays[0].play_description == "S6/G6"
    assert editor.mode == "detail"
    assert editor.modifier_selection_active is True
    assert editor.selected_modifier_group == "h"


def test_detail_mode_complete_workflow(tmp_path):
    """Test complete detail mode workflow with automatic progression."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Add a play to work with
    test_game = event_file.games[0]
    test_game.plays.append(
        Play(
            inning=1,
            team=0,
            batter_id="test0001",
            count="00",
            pitches="",
            play_description="",
        )
    )

    # Enter detail mode
    editor._enter_detail_mode("S")

    # Select hit type and fielding position - should automatically save and progress
    editor._handle_detail_mode_input("g")  # Grounder
    editor._handle_detail_mode_input("6")  # Shortstop

    # Check that the play description was set correctly and we're now in Hit Location builder
    assert test_game.plays[0].play_description == "S6/G6"
    assert editor.mode == "detail"
    assert editor.modifier_selection_active is True
    assert editor.selected_modifier_group == "h"


def test_generate_detailed_play_description(tmp_path):
    """Test generating detailed play descriptions."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Test various combinations
    test_cases = [
        ("S", "G", 6, "S6/G6"),  # Single, grounder, shortstop
        ("S", "G", 0, "S/G"),  # Single, grounder, no position
        ("D", "L", 7, "D7/L7"),  # Double, line drive, left field
        ("D", "L", 0, "D/L"),  # Double, line drive, no position
        ("T", "F", 8, "T8/F8"),  # Triple, fly ball, center field
        ("T", "F", 0, "T/F"),  # Triple, fly ball, no position
        ("HR", "F", 7, "HR/F7"),  # Home run, fly ball, left field
        ("HR", "F", 0, "HR/F"),  # Home run, fly ball, no position
        ("E", "G", 6, "E6/G6"),  # Error, grounder, shortstop
        ("E", "G", 0, "E/G"),  # Error, grounder, no position
        ("FC", "G", 4, "FC4/G4"),  # Fielder's choice, grounder, second base
        ("FC", "G", 0, "FC/G"),  # Fielder's choice, no position
        ("SF", "F", 8, "SF8/F8"),  # Sacrifice fly, fly ball, center field
        ("SF", "F", 0, "SF/F"),  # Sacrifice fly, no position
        ("SH", "B", 1, "SH1/B1"),  # Sacrifice bunt, bunt, pitcher
        ("SH", "B", 0, "SH/B"),  # Sacrifice bunt, no position
    ]

    for result, hit_type, position, expected in test_cases:
        actual = editor._generate_detailed_play_description(result, hit_type, position)
        assert (
            actual == expected
        ), f"Expected {expected} for {result}/{hit_type}/{position}, got {actual}"


def test_detail_mode_incomplete_selection(tmp_path):
    """Test that incomplete selections don't save."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Add a play to work with
    test_game = event_file.games[0]
    test_game.plays.append(
        Play(
            inning=1,
            team=0,
            batter_id="test0001",
            count="00",
            pitches="",
            play_description="",
        )
    )

    # Enter detail mode
    editor._enter_detail_mode("S")

    # Try to save without selecting hit type
    editor._save_detail_mode_result()
    assert test_game.plays[0].play_description == ""  # Should not be set
    assert editor.mode == "detail"  # Should stay in detail mode

    # Select hit type but not fielding position; saving should now be allowed and omit position
    editor._handle_detail_mode_input("g")
    editor._save_detail_mode_result()
    assert test_game.plays[0].play_description == "S/G"  # Saved with no position
    # Should remain in detail mode with Hit Location builder active
    assert editor.mode == "detail"
    assert editor.modifier_selection_active is True
    assert editor.selected_modifier_group == "h"


def test_reset_detail_mode(tmp_path):
    """Test resetting detail mode state."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Set up detail mode state
    editor.detail_mode_result = "S"
    editor.detail_mode_hit_type = "G"
    editor.detail_mode_fielders = [6]

    # Reset
    editor._reset_detail_mode()

    assert editor.detail_mode_result is None
    assert editor.detail_mode_hit_type is None
    assert editor.detail_mode_fielders == []


def test_detail_mode_hotkeys(tmp_path):
    """Test that all detail mode hotkeys are properly mapped."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Test hit type hotkeys
    expected_hit_types = {
        "g": "G",  # Grounder
        "l": "L",  # Line drive
        "f": "F",  # Fly ball
        "p": "P",  # Pop up
        "b": "B",  # Bunt
    }

    for key, expected in expected_hit_types.items():
        assert key in editor.hit_type_hotkeys
        assert editor.hit_type_hotkeys[key] == expected

    # Test fielding position hotkeys
    expected_positions = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
    }

    for key, expected in expected_positions.items():
        assert key in editor.fielding_position_hotkeys
        assert editor.fielding_position_hotkeys[key] == expected


def test_detail_mode_integration(tmp_path):
    """Test that detail mode integrates correctly with the main editor workflow."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Add a play to work with
    test_game = event_file.games[0]
    test_game.plays.append(
        Play(
            inning=1,
            team=0,
            batter_id="test0001",
            count="00",
            pitches="",
            play_description="",
        )
    )

    # Start in pitch mode
    assert editor.mode == "pitch"

    # Switch to play mode
    editor.mode = "play"
    assert editor.mode == "play"

    # Simulate selecting a play result (this would normally be done via key input)
    editor._enter_detail_mode("S")
    assert editor.mode == "detail"
    assert editor.detail_mode_result == "S"

    # Simulate selecting hit type and fielding position
    editor._handle_detail_mode_input("g")  # Grounder
    editor._handle_detail_mode_input("6")  # Shortstop

    # Save the result
    editor._save_detail_mode_result()

    # Should remain in detail mode with Hit Location builder active
    assert editor.mode == "detail"
    assert test_game.plays[0].play_description == "S6/G6"
    assert editor.modifier_selection_active is True
    assert editor.selected_modifier_group == "h"


def test_detail_mode_tab_exit(tmp_path):
    """Test that TAB key exits detail mode correctly."""
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Enter detail mode
    editor._enter_detail_mode("S")
    assert editor.mode == "detail"

    # Simulate TAB key press (this would normally be done via key input)
    editor.mode = "play"  # Simulate TAB switching
    editor._reset_detail_mode()

    # Should be back in play mode with reset state
    assert editor.mode == "play"
    assert editor.detail_mode_result is None
    assert editor.detail_mode_hit_type is None
    assert editor.detail_mode_fielding_position is None


def test_detail_mode_automatic_progression(tmp_path):
    """Test that the editor automatically progresses to the next batter after selecting fielding position."""
    # Create a simple event file with multiple plays
    game = Game(
        game_id="TEST001",
        info=GameInfo(),
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="ATL001",
                count="",
                pitches="",
                play_description="",
            ),
            Play(
                inning=1,
                team=0,
                batter_id="ATL002",
                count="",
                pitches="",
                play_description="",
            ),
            Play(
                inning=1,
                team=0,
                batter_id="ATL003",
                count="",
                pitches="",
                play_description="",
            ),
        ],
    )

    event_file = EventFile(games=[game])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Start at the first play
    editor.current_game_index = 0
    editor.current_play_index = 0

    # Enter detail mode with a single
    editor._enter_detail_mode("S")
    assert editor.mode == "detail"
    assert editor.current_play_index == 0

    # Select hit type and fielding position - progression should happen automatically after fielding position
    editor._handle_detail_mode_input("g")  # Grounder
    editor._handle_detail_mode_input(
        "6"
    )  # Shortstop - this should automatically save and progress

    # Now we should be in Hit Location builder; no auto-advance yet
    assert editor.mode == "detail"
    assert editor.modifier_selection_active is True
    assert editor.selected_modifier_group == "h"

    # Verify the play description was saved correctly
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description == "S6/G6"
