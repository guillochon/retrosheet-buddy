"""Tests to ensure no navigation shortcut conflicts exist."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor, validate_shortcuts
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_no_navigation_conflicts():
    """Test that no navigation shortcut conflicts exist."""
    # This should not raise any exceptions
    validate_shortcuts()


def test_navigation_keys_have_exclusive_access(tmp_path):
    """Test that navigation keys are not used by any mode."""
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

    # Define navigation keys that must be exclusive
    navigation_keys = {"q", "left", "right", "tab", "x", "-", "\r", "\n"}

    # Check pitch mode doesn't use navigation keys
    pitch_keys = set(editor.pitch_hotkeys.keys())
    pitch_conflicts = navigation_keys & pitch_keys
    assert (
        len(pitch_conflicts) == 0
    ), f"Pitch mode uses navigation keys: {pitch_conflicts}"

    # Check play mode doesn't use navigation keys
    play_keys = set(editor.play_hotkeys.keys())
    play_conflicts = navigation_keys & play_keys
    assert len(play_conflicts) == 0, f"Play mode uses navigation keys: {play_conflicts}"

    # Check detail mode doesn't use navigation keys
    hit_type_keys = set(editor.hit_type_hotkeys.keys())
    fielding_keys = set(editor.fielding_position_hotkeys.keys())
    out_type_keys = set(editor.out_type_hotkeys.keys())
    detail_keys = hit_type_keys | fielding_keys | out_type_keys
    detail_conflicts = navigation_keys & detail_keys
    assert (
        len(detail_conflicts) == 0
    ), f"Detail mode uses navigation keys: {detail_conflicts}"


def test_changed_key_mappings_work(tmp_path):
    """Test that the changed key mappings work correctly."""
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

    # Test the changed pitch mode key: * for Swinging on pitchout
    assert "*" in editor.pitch_hotkeys, "Asterisk key should be in pitch_hotkeys"
    assert (
        editor.pitch_hotkeys["*"] == "Q"
    ), "Asterisk should map to Q (Swinging on pitchout)"

    # Test that 'q' is no longer in pitch mode (it's reserved for navigation Quit)
    assert (
        "q" not in editor.pitch_hotkeys
    ), "Q key should not be in pitch_hotkeys (reserved for navigation)"

    # The GDP key was moved to the Out Type wizard; '#' no longer in play hotkeys
    assert "#" not in editor.play_hotkeys

    # Test that 'x' is no longer in play mode (it's reserved for navigation Undo)
    assert (
        "x" not in editor.play_hotkeys
    ), "X key should not be in play_hotkeys (reserved for navigation)"

    # Test the changed detail mode key: ! for Lined into double play
    assert (
        "!" in editor.out_type_hotkeys
    ), "Exclamation key should be in out_type_hotkeys"
    assert (
        editor.out_type_hotkeys["!"] == "LDP"
    ), "Exclamation should map to LDP (Lined into double play)"

    # Test that 'x' is no longer in detail mode out types
    assert (
        "x" not in editor.out_type_hotkeys
    ), "X key should not be in out_type_hotkeys (reserved for navigation)"


def test_new_keys_functionality(tmp_path):
    """Test that the new symbol keys work functionally."""
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

    # Test * key adds Q pitch (Swinging on pitchout)
    initial_pitches = test_game.plays[0].pitches
    if editor.mode == "pitch" and "*" in editor.pitch_hotkeys:
        editor._add_pitch(editor.pitch_hotkeys["*"])

    assert (
        test_game.plays[0].pitches == initial_pitches + "Q"
    ), "Asterisk key should add Q pitch"

    # Reset for next test
    test_game.plays[0].pitches = ""
    test_game.plays[0].play_description = ""

    # GDP is selected in detail mode, not play mode
    assert editor.out_type_hotkeys.get("w") == "GDP"

    # Test ! key works for LDP in detail mode
    assert (
        editor.out_type_hotkeys.get("!") == "LDP"
    ), "Exclamation key should map to LDP for detail mode"


def test_description_mappings_updated(tmp_path):
    """Test that the description mappings reflect the new keys."""
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

    # Test pitch descriptions
    pitch_descriptions = editor._get_pitch_descriptions()
    assert (
        pitch_descriptions.get("Q") == "Swinging on pitchout"
    ), "Q pitch description should be correct"

    # Test play descriptions
    play_descriptions = editor._get_play_descriptions()
    assert (
        play_descriptions.get("GDP") == "Grounded into DP"
    ), "GDP description should be correct"

    # Test out type descriptions
    out_type_descriptions = editor._get_out_type_descriptions()
    assert (
        out_type_descriptions.get("LDP") == "Lined into double play"
    ), "LDP description should be correct"


def test_navigation_keys_still_work(tmp_path):
    """Test that navigation keys still work as expected."""
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

    # Test that 'q' is still available for Quit (navigation)
    # (We can't test actual quit without exiting, but we can verify it's not used by modes)
    assert "q" not in editor.pitch_hotkeys
    assert "q" not in editor.play_hotkeys

    # Test that 'x' is still available for Undo (navigation)
    # Add a pitch, then undo
    editor._add_pitch("B")
    assert test_game.plays[0].pitches == "B"

    # Simulate 'x' key press for undo
    editor._undo_last_action()
    assert test_game.plays[0].pitches == "", "X key should trigger undo successfully"


def test_auto_mode_switch_on_navigation(tmp_path):
    """When moving between plays, auto-switch modes based on play content."""
    game = Game(
        game_id="TESTNAV",
        info=GameInfo(),
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="A",
                count="00",
                pitches="",
                play_description="",
            ),  # empty
            Play(
                inning=1,
                team=0,
                batter_id="B",
                count="00",
                pitches="B",
                play_description="",
            ),  # pitches only
            Play(
                inning=1,
                team=0,
                batter_id="C",
                count="00",
                pitches="B",
                play_description="W",
            ),  # both
        ],
    )
    event_file = EventFile(games=[game])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Start at play 1 (index 0). Empty -> should be in pitch mode regardless of prior.
    editor.mode = "detail"
    editor._next_play()  # move to index 1
    # After moving from empty (prior was detail), index 1 has pitches but no result -> play mode
    assert editor.current_play_index == 1
    assert editor.mode == "play"

    # Move to index 2 which has both -> keep prior mode (play)
    editor._next_play()
    assert editor.current_play_index == 2
    assert editor.mode == "play"

    # Go back to index 1 which has pitches only -> switch to play mode (stays play)
    editor._previous_play()
    assert editor.current_play_index == 1
    assert editor.mode == "play"

    # Go back to index 0 which is empty -> switch to pitch mode
    editor._previous_play()
    assert editor.current_play_index == 0
    assert editor.mode == "pitch"
