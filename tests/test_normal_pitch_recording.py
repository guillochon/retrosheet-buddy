"""Tests for normal pitch recording functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_normal_pitch_recording(tmp_path):
    """Test that normal pitch recording works without triggering auto walk/strikeout."""
    # Create test game with a play
    test_game = Game(
        game_id="TEST004",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")
        ]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]
    
    # Add some pitches that don't reach walk/strikeout
    editor._add_pitch('B')  # Ball
    editor._add_pitch('S')  # Called strike
    editor._add_pitch('F')  # Foul
    editor._add_pitch('B')  # Another ball
    
    # Check that no automatic result was set
    assert current_play.play_description == "", f"Expected no result, got {current_play.play_description}"
    assert current_play.count == "22", f"Expected 22, got {current_play.count}"
    assert current_play.pitches == "BSFB", f"Expected BSFB, got {current_play.pitches}"
    
    # Check that we're still on the same play
    assert editor.current_play_index == 0, f"Expected to stay on same play, but moved to {editor.current_play_index}"


def test_foul_ball_behavior(tmp_path):
    """Test that foul balls don't count as strikes after 2 strikes."""
    # Create test game with a play
    test_game = Game(
        game_id="TEST005",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(inning=1, team=0, batter_id="TEST1", count="00", pitches="", play_description="")
        ]
    )
    
    test_event_file = EventFile(games=[test_game])
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start with first play
    editor.current_play_index = 0
    current_play = test_game.plays[0]
    
    # Add 2 strikes first
    editor._add_pitch('S')  # First strike
    editor._add_pitch('S')  # Second strike
    
    # Add foul balls - they shouldn't count as strikes after 2 strikes
    for i in range(3):
        editor._add_pitch('F')
    
    # Check that count is still 2 strikes
    assert current_play.count == "02", f"Expected 02, got {current_play.count}"
    assert current_play.play_description == "", f"Expected no result, got {current_play.play_description}" 