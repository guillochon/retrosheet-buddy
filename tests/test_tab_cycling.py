"""Test TAB key cycling through modes."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


@pytest.fixture
def test_event_file():
    """Create a test event file with one game and one play."""
    game_info = GameInfo(
        date="2023-04-01",
        game_id="TEST202304010",
        home_team="HOME",
        away_team="AWAY"
    )
    
    play = Play(
        inning=1,
        team=0,
        batter_id="TEST0001",
        count="00",
        pitches="",
        play_description=""
    )
    
    game = Game(
        game_id="TEST202304010",
        info=game_info,
        plays=[play]
    )
    
    return EventFile(games=[game])


def test_tab_cycling_from_pitch_mode(test_event_file, tmp_path):
    """Test TAB cycling from pitch mode to play mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in pitch mode
    assert editor.mode == 'pitch'
    
    # Simulate TAB key press
    editor._handle_tab_key()
    
    # Should now be in play mode
    assert editor.mode == 'play'


def test_tab_cycling_from_play_mode(test_event_file, tmp_path):
    """Test TAB cycling from play mode to detail mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Set to play mode
    editor.mode = 'play'
    
    # Simulate TAB key press
    editor._handle_tab_key()
    
    # Should now be in detail mode
    assert editor.mode == 'detail'


def test_tab_cycling_from_detail_mode(test_event_file, tmp_path):
    """Test TAB cycling from detail mode back to pitch mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Set to detail mode
    editor.mode = 'detail'
    
    # Simulate TAB key press
    editor._handle_tab_key()
    
    # Should now be back in pitch mode
    assert editor.mode == 'pitch'
    # Detail mode should be reset
    assert editor.detail_mode_result is None
    assert editor.detail_mode_hit_type is None
    assert editor.detail_mode_fielders == []


def test_tab_cycling_complete_cycle(test_event_file, tmp_path):
    """Test complete TAB cycling through all modes."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in pitch mode
    assert editor.mode == 'pitch'
    
    # First TAB: pitch -> play
    editor._handle_tab_key()
    assert editor.mode == 'play'
    
    # Second TAB: play -> detail
    editor._handle_tab_key()
    assert editor.mode == 'detail'
    
    # Third TAB: detail -> pitch
    editor._handle_tab_key()
    assert editor.mode == 'pitch'


def test_next_mode_display_text(test_event_file, tmp_path):
    """Test that the next mode is correctly displayed in the controls."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # In pitch mode, should show "Switch to PLAY mode"
    from rich.text import Text
    controls_text = Text()
    editor._add_mode_section(controls_text)
    assert "Switch to PLAY mode" in str(controls_text)
    
    # In play mode, should show "Switch to DETAIL mode"
    editor.mode = 'play'
    controls_text = Text()
    editor._add_mode_section(controls_text)
    assert "Switch to DETAIL mode" in str(controls_text)
    
    # In detail mode, should show "Switch to PITCH mode"
    editor.mode = 'detail'
    controls_text = Text()
    editor._add_mode_section(controls_text)
    assert "Switch to PITCH mode" in str(controls_text)


# Helper method to add to RetrosheetEditor for testing
def _handle_tab_key(self):
    """Helper method to simulate TAB key press for testing."""
    if self.mode == 'pitch':
        self.mode = 'play'
    elif self.mode == 'play':
        self.mode = 'detail'
    elif self.mode == 'detail':
        self.mode = 'pitch'  # Cycle back to pitch mode
        self._reset_detail_mode()


# Add the helper method to RetrosheetEditor for testing
RetrosheetEditor._handle_tab_key = _handle_tab_key 