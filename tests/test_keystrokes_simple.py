"""Tests for keystroke functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_keystroke_mappings():
    """Test that all keystroke mappings are correct and conflict-free."""
    # Create test data
    test_game = Game(
        game_id="TEST001",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, Path("test_outputs"))
    
    # Test pitch keystrokes
    pitch_tests = [
        ('b', 'B', 'Ball'),
        ('s', 'S', 'Strike'),
        ('f', 'F', 'Foul'),
        ('c', 'C', 'Called strike'),
        ('w', 'W', 'Swinging strike'),
        ('t', 'T', 'Foul tip'),
        ('m', 'M', 'Missed bunt'),
        ('p', 'P', 'Pitchout'),
        ('i', 'I', 'Intentional ball'),
        ('h', 'H', 'Hit batter'),
        ('v', 'V', 'Wild pitch'),
        ('a', 'A', 'Passed ball'),
        ('q', 'Q', 'Swinging on pitchout'),
        ('r', 'R', 'Foul on pitchout'),
        ('e', 'E', 'Foul bunt'),
        ('n', 'N', 'No pitch'),
        ('o', 'O', 'Foul on bunt'),
        ('u', 'U', 'Unknown'),
    ]
    
    for key, expected, description in pitch_tests:
        if key in editor.pitch_hotkeys:
            result = editor.pitch_hotkeys[key]
            assert result == expected, f"Pitch key '{key}' ({description}) should be '{expected}', got '{result}'"
        else:
            assert False, f"Pitch key '{key}' ({description}) not found in pitch_hotkeys"
    
    # Test play result keystrokes
    play_tests = [
        ('1', 'S1', 'Single'),
        ('2', 'D2', 'Double'),
        ('3', 'T3', 'Triple'),
        ('4', 'HR', 'Home run'),
        ('k', 'K', 'Strikeout'),
        ('l', 'W', 'Walk'),
        ('y', 'HP', 'Hit by pitch'),
        ('z', 'E', 'Error'),
        ('g', 'FC', 'Fielder\'s choice'),
        ('j', 'DP', 'Double play'),
        ('5', 'TP', 'Triple play'),
        ('6', 'SF', 'Sacrifice fly'),
        ('7', 'SH', 'Sacrifice bunt'),
        ('8', 'IW', 'Intentional walk'),
        ('9', 'CI', 'Catcher interference'),
        ('0', 'OA', 'Out advancing'),
        (';', 'ND', 'No play'),
    ]
    
    for key, expected, description in play_tests:
        if key in editor.play_hotkeys:
            result = editor.play_hotkeys[key]
            assert result == expected, f"Play key '{key}' ({description}) should be '{expected}', got '{result}'"
        else:
            assert False, f"Play key '{key}' ({description}) not found in play_hotkeys"
    
    # Check for conflicts
    pitch_keys = set(editor.pitch_hotkeys.keys())
    play_keys = set(editor.play_hotkeys.keys())
    conflicts = pitch_keys & play_keys
    
    assert len(conflicts) == 0, f"Key conflicts found: {conflicts}"


def test_mode_functionality():
    """Test mode switching functionality."""
    # Create test data
    test_game = Game(
        game_id="TEST001",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, Path("test_outputs"))
    
    # Test initial mode
    assert editor.mode == "pitch", "Should start in pitch mode"
    
    # Test mode switching
    editor.mode = "play" if editor.mode == "pitch" else "pitch"
    assert editor.mode == "play", "Should switch to play mode"
    
    editor.mode = "play" if editor.mode == "pitch" else "pitch"
    assert editor.mode == "pitch", "Should switch back to pitch mode"


def test_pitch_functionality():
    """Test pitch recording functionality."""
    # Create test data
    test_game = Game(
        game_id="TEST001",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, Path("test_outputs"))
    
    # Test adding pitches
    editor._add_pitch('S')
    assert test_game.plays[0].pitches == 'S', "Should add strike"
    
    editor._add_pitch('B')
    assert test_game.plays[0].pitches == 'SB', "Should add ball after strike"


def test_play_result_functionality():
    """Test play result setting functionality."""
    # Create test data
    test_game = Game(
        game_id="TEST001",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, Path("test_outputs"))
    
    # Test setting play results
    editor._set_play_result('S1')
    assert test_game.plays[0].play_description == 'S1', "Should set single"
    
    editor._set_play_result('HR')
    assert test_game.plays[0].play_description == 'HR', "Should set home run"


def test_undo_functionality():
    """Test undo functionality."""
    # Create test data
    test_game = Game(
        game_id="TEST001",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, Path("test_outputs"))
    
    # Test undo with no history
    initial_pitches = test_game.plays[0].pitches
    initial_result = test_game.plays[0].play_description
    editor._undo_last_action()
    
    # Test undo after adding pitch
    editor._add_pitch('S')
    assert test_game.plays[0].pitches == 'S', "Should add strike"
    
    editor._undo_last_action()
    assert test_game.plays[0].pitches == '', "Should undo to empty pitches"
    
    # Test undo after setting play result
    editor._set_play_result('S1')
    assert test_game.plays[0].play_description == 'S1', "Should set single"
    
    editor._undo_last_action()
    assert test_game.plays[0].play_description == '', "Should undo to empty result" 