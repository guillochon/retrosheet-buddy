"""Tests for keystroke functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor, validate_shortcuts
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_shortcut_validation():
    """Test that shortcut validation works correctly."""
    # This should pass without conflicts
    validate_shortcuts()


def test_shortcut_validation_with_conflicts():
    """Test that shortcut validation detects conflicts."""
    # Import the function to test it directly
    from retrosheet_buddy.editor import validate_shortcuts

    # The current implementation should not have conflicts
    # If conflicts are introduced, this test will catch them
    try:
        validate_shortcuts()
    except ValueError as e:
        # If conflicts are found, the error message should be informative
        assert "Shortcut conflicts detected" in str(e)
        assert "Please resolve these conflicts" in str(e)
        pytest.fail(f"Shortcut conflicts detected: {e}")


def test_shortcut_validation_startup():
    """Test that shortcut validation works when called directly."""
    # Simply test that we can call validate_shortcuts without errors
    # This verifies the validation logic works correctly
    try:
        validate_shortcuts()
        # If we get here without exception, validation passed
        assert True, "validate_shortcuts should complete without errors"
    except ValueError as e:
        # If there are actual conflicts, this is a real issue that should be addressed
        pytest.fail(f"Shortcut validation failed: {e}")


def test_keystroke_mappings(tmp_path):
    """Test that all keystroke mappings are correct and conflict-free."""
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

    # Test pitch keystrokes
    pitch_tests = [
        ("b", "B", "Ball"),
        ("s", "S", "Swinging strike"),
        ("f", "F", "Foul"),
        ("c", "C", "Called strike"),
        ("t", "T", "Foul tip"),
        ("m", "M", "Missed bunt"),
        ("p", "P", "Pitchout"),
        ("i", "I", "Intentional ball"),
        ("h", "H", "Hit batter"),
        ("v", "V", "Wild pitch"),
        ("a", "A", "Passed ball"),
        ("*", "Q", "Swinging on pitchout"),
        ("r", "R", "Foul on pitchout"),
        ("e", "E", "Foul bunt"),
        ("n", "N", "No pitch"),
        ("o", "O", "Foul on bunt"),
        ("u", "U", "Unknown"),
    ]

    for key, expected, description in pitch_tests:
        if key in editor.pitch_hotkeys:
            result = editor.pitch_hotkeys[key]
            assert (
                result == expected
            ), f"Pitch key '{key}' ({description}) should be '{expected}', got '{result}'"
        else:
            assert (
                False
            ), f"Pitch key '{key}' ({description}) not found in pitch_hotkeys"

    # Test play result keystrokes
    play_tests = [
        ("1", "S", "Single"),
        ("2", "D", "Double"),
        ("3", "T", "Triple"),
        ("4", "HR", "Home run"),
        ("l", "W", "Walk"),
        ("y", "HP", "Hit by pitch"),
        ("z", "E", "Error"),
        ("8", "IW", "Intentional walk"),
        ("9", "CI", "Catcher interference"),
        ("0", "OA", "Out advancing"),
        (";", "ND", "No play"),
        ("w", "OUT", "Out (opens wizard)"),
    ]

    for key, expected, description in play_tests:
        if key in editor.play_hotkeys:
            result = editor.play_hotkeys[key]
            assert (
                result == expected
            ), f"Play key '{key}' ({description}) should be '{expected}', got '{result}'"
        else:
            assert False, f"Play key '{key}' ({description}) not found in play_hotkeys"

    # Check for conflicts
    pitch_keys = set(editor.pitch_hotkeys.keys())
    play_keys = set(editor.play_hotkeys.keys())
    conflicts = pitch_keys & play_keys
    # Allow 'l' to overlap intentionally: 'l' is Called strike in pitch mode and Walk in play mode
    allowed_overlap = {"l"}
    conflicts = {k for k in conflicts if k not in allowed_overlap}
    assert len(conflicts) == 0, f"Key conflicts found: {conflicts}"


def test_mode_functionality(tmp_path):
    """Test mode switching functionality."""
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

    # Test initial mode
    assert editor.mode == "pitch", "Should start in pitch mode"

    # Test mode switching
    editor.mode = "play" if editor.mode == "pitch" else "pitch"
    assert editor.mode == "play", "Should switch to play mode"

    editor.mode = "play" if editor.mode == "pitch" else "pitch"
    assert editor.mode == "pitch", "Should switch back to pitch mode"


def test_pitch_functionality(tmp_path):
    """Test pitch recording functionality."""
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

    # Test adding pitches
    editor._add_pitch("S")
    assert test_game.plays[0].pitches == "S", "Should add strike"

    editor._add_pitch("B")
    assert test_game.plays[0].pitches == "SB", "Should add ball after strike"


def test_play_result_functionality(tmp_path):
    """Test play result setting functionality."""
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

    # Test setting play results
    editor._set_play_result("S")
    assert (
        test_game.plays[0].play_description == "S8/G6"
    ), "Should set single in Retrosheet format"

    editor._set_play_result("HR")
    assert (
        test_game.plays[0].play_description == "HR/F7"
    ), "Should set home run in Retrosheet format"


def test_clear_in_pitch_and_play_modes(tmp_path):
    """Test context-sensitive clear functionality with '-' key mapping behavior."""
    # Create test data
    test_game = Game(
        game_id="TESTCLR",
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

    # Start in pitch mode, add some pitches
    assert editor.mode == "pitch"
    editor._add_pitch("B")
    editor._add_pitch("S")
    assert test_game.plays[0].pitches == "BS"
    assert test_game.plays[0].count == "11"

    # Clear pitches
    editor._clear_pitches()
    assert test_game.plays[0].pitches == ""
    assert test_game.plays[0].count == "00"

    # Switch to play mode and set a result
    editor.mode = "play"
    editor._set_play_result("W")
    assert test_game.plays[0].play_description == "W"

    # Clear play result
    editor._clear_play_result()
    assert test_game.plays[0].play_description == ""


def test_undo_functionality(tmp_path):
    """Test undo functionality."""
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

    # Test undo with no history
    initial_pitches = test_game.plays[0].pitches
    initial_result = test_game.plays[0].play_description
    editor._undo_last_action()

    # Test undo after adding pitch
    editor._add_pitch("S")
    assert test_game.plays[0].pitches == "S", "Should add strike"

    editor._undo_last_action()
    assert test_game.plays[0].pitches == "", "Should undo to empty pitches"

    # Test undo after setting play result
    editor._set_play_result("S")
    assert (
        test_game.plays[0].play_description == "S8/G6"
    ), "Should set single in Retrosheet format"

    editor._undo_last_action()
    assert test_game.plays[0].play_description == "", "Should undo to empty result"
