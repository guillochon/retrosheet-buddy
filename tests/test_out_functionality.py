"""Test out functionality in detail mode."""

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


def test_out_play_hotkeys(test_event_file, tmp_path):
    """Test that out play hotkeys are correctly defined."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Check that out play hotkeys exist in the consolidated play_hotkeys
    assert 'w' in editor.play_hotkeys
    assert '#' in editor.play_hotkeys
    assert 'd' in editor.play_hotkeys
    assert '[' in editor.play_hotkeys
    assert ']' in editor.play_hotkeys
    
    # Check that they map to correct values
    assert editor.play_hotkeys['w'] == 'OUT'
    assert editor.play_hotkeys['#'] == 'GDP'
    assert editor.play_hotkeys['d'] == 'LDP'
    assert editor.play_hotkeys['['] == 'FO'
    assert editor.play_hotkeys[']'] == 'UO'


def test_out_type_hotkeys(test_event_file, tmp_path):
    """Test that out type hotkeys are correctly defined."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Check that out type hotkeys exist
    assert 'g' in editor.out_type_hotkeys
    assert 'l' in editor.out_type_hotkeys
    assert 'f' in editor.out_type_hotkeys
    assert 'p' in editor.out_type_hotkeys
    assert 'b' in editor.out_type_hotkeys
    assert 's' in editor.out_type_hotkeys
    assert 'h' in editor.out_type_hotkeys
    assert 'w' in editor.out_type_hotkeys
    assert '!' in editor.out_type_hotkeys
    assert 'y' in editor.out_type_hotkeys
    assert 'z' in editor.out_type_hotkeys
    assert '[' in editor.out_type_hotkeys
    
    # Check that they map to correct values
    assert editor.out_type_hotkeys['g'] == 'G'
    assert editor.out_type_hotkeys['l'] == 'L'
    assert editor.out_type_hotkeys['f'] == 'F'
    assert editor.out_type_hotkeys['p'] == 'P'
    assert editor.out_type_hotkeys['b'] == 'B'
    assert editor.out_type_hotkeys['s'] == 'SF'
    assert editor.out_type_hotkeys['h'] == 'SH'
    assert editor.out_type_hotkeys['w'] == 'GDP'
    assert editor.out_type_hotkeys['!'] == 'LDP'
    assert editor.out_type_hotkeys['y'] == 'TP'
    assert editor.out_type_hotkeys['z'] == 'FO'
    assert editor.out_type_hotkeys['['] == 'UO'


def test_out_detail_mode_workflow(test_event_file, tmp_path):
    """Test the complete workflow for entering an out in detail mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in play mode
    editor.mode = 'play'
    
    # Simulate selecting OUT play type
    editor._enter_detail_mode('OUT')
    assert editor.mode == 'detail'
    assert editor.detail_mode_result == 'OUT'
    assert editor.detail_mode_out_type is None
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting ground out type
    editor._handle_detail_mode_input('g')
    assert editor.detail_mode_out_type == 'G'
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting fielding position (shortstop)
    editor._handle_detail_mode_input('6')
    
    # Should not automatically save - need to press ENTER
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description == ''  # Not saved yet
    assert editor.mode == 'detail'  # Still in detail mode
    assert editor.detail_mode_fielders == [6]  # Fielder added to list
    
    # Now simulate pressing ENTER to save
    editor._save_detail_mode_result()
    
    # Should now be saved but remain in detail mode (no auto-advance)
    assert current_play.play_description == '6/G'
    assert editor.mode == 'detail'


def test_gdp_detail_mode_workflow(test_event_file, tmp_path):
    """Test the complete workflow for entering a GDP in detail mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in play mode
    editor.mode = 'play'
    
    # Simulate selecting GDP play type
    editor._enter_detail_mode('GDP')
    assert editor.mode == 'detail'
    assert editor.detail_mode_result == 'GDP'
    assert editor.detail_mode_out_type is None
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting ground out type
    editor._handle_detail_mode_input('g')
    assert editor.detail_mode_out_type == 'G'
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting fielding position (shortstop)
    editor._handle_detail_mode_input('6')
    
    # Should not automatically save - need to press ENTER
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description == ''  # Not saved yet
    assert editor.mode == 'detail'  # Still in detail mode
    assert editor.detail_mode_fielders == [6]  # Fielder added to list
    
    # Now simulate pressing ENTER to save
    editor._save_detail_mode_result()
    
    # Should now be saved but remain in detail mode (no auto-advance)
    assert current_play.play_description == '6/G/GDP'
    assert editor.mode == 'detail'


def test_ldp_detail_mode_workflow(test_event_file, tmp_path):
    """Test the complete workflow for entering a LDP in detail mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in play mode
    editor.mode = 'play'
    
    # Simulate selecting LDP play type
    editor._enter_detail_mode('LDP')
    assert editor.mode == 'detail'
    assert editor.detail_mode_result == 'LDP'
    assert editor.detail_mode_out_type is None
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting line out type
    editor._handle_detail_mode_input('l')
    assert editor.detail_mode_out_type == 'L'
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting fielding position (center field)
    editor._handle_detail_mode_input('8')
    
    # Should not automatically save - need to press ENTER
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description == ''  # Not saved yet
    assert editor.mode == 'detail'  # Still in detail mode
    assert editor.detail_mode_fielders == [8]  # Fielder added to list
    
    # Now simulate pressing ENTER to save
    editor._save_detail_mode_result()
    
    # Should now be saved but remain in detail mode (no auto-advance)
    assert current_play.play_description == '8/L/LDP'
    assert editor.mode == 'detail'


def test_regular_hit_detail_mode_unchanged(test_event_file, tmp_path):
    """Test that regular hits still work the same way in detail mode."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in play mode
    editor.mode = 'play'
    
    # Simulate selecting single
    editor._enter_detail_mode('S')
    assert editor.mode == 'detail'
    assert editor.detail_mode_result == 'S'
    assert editor.detail_mode_hit_type is None
    assert editor.detail_mode_fielding_position is None
    
    # Simulate selecting grounder hit type
    editor._handle_detail_mode_input('g')
    assert editor.detail_mode_hit_type == 'G'
    assert editor.detail_mode_fielding_position is None
    
    # Simulate selecting fielding position (shortstop)
    editor._handle_detail_mode_input('6')
    
    # Should automatically save and progress
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description == 'S6/G6'
    assert editor.mode == 'pitch'  # Should return to pitch mode
    
    # After reset, all detail mode variables should be None
    assert editor.detail_mode_result is None
    assert editor.detail_mode_hit_type is None
    assert editor.detail_mode_fielding_position is None


def test_out_play_descriptions(test_event_file, tmp_path):
    """Test that out play descriptions are correctly defined."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    descriptions = editor._get_play_descriptions()
    
    assert 'OUT' in descriptions
    assert 'GDP' in descriptions
    assert 'LDP' in descriptions
    assert 'FO' in descriptions
    assert 'UO' in descriptions
    
    assert descriptions['OUT'] == 'Out'
    assert descriptions['GDP'] == 'Grounded into DP'
    assert descriptions['LDP'] == 'Lined into DP'
    assert descriptions['FO'] == 'Force out'
    assert descriptions['UO'] == 'Unassisted out'


def test_multiple_fielders_sequential_selection(test_event_file, tmp_path):
    """Test that multiple fielders can be selected sequentially for out plays."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    # Start in play mode
    editor.mode = 'play'
    
    # Simulate selecting GDP play type
    editor._enter_detail_mode('GDP')
    assert editor.mode == 'detail'
    assert editor.detail_mode_result == 'GDP'
    
    # Simulate selecting ground out type
    editor._handle_detail_mode_input('g')
    assert editor.detail_mode_out_type == 'G'
    assert editor.detail_mode_fielders == []
    
    # Simulate selecting first fielder (shortstop)
    editor._handle_detail_mode_input('6')
    assert editor.detail_mode_fielders == [6]
    assert editor.mode == 'detail'  # Still in detail mode
    
    # Simulate selecting second fielder (second base)
    editor._handle_detail_mode_input('4')
    assert editor.detail_mode_fielders == [6, 4]
    assert editor.mode == 'detail'  # Still in detail mode
    
    # Simulate selecting third fielder (first base)
    editor._handle_detail_mode_input('3')
    assert editor.detail_mode_fielders == [6, 4, 3]
    assert editor.mode == 'detail'  # Still in detail mode
    
    # Now simulate pressing ENTER to save
    editor._save_detail_mode_result()
    
    # Should now be saved with all fielders and remain in detail mode
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description == '643/G/GDP'  # 6-4-3 double play
    assert editor.mode == 'detail'


def test_out_type_descriptions(test_event_file, tmp_path):
    """Test that out type descriptions are correctly defined."""
    editor = RetrosheetEditor(test_event_file, tmp_path)
    
    descriptions = editor._get_out_type_descriptions()
    
    assert 'G' in descriptions
    assert 'L' in descriptions
    assert 'F' in descriptions
    assert 'P' in descriptions
    assert 'B' in descriptions
    assert 'SF' in descriptions
    assert 'SH' in descriptions
    assert 'GDP' in descriptions
    assert 'LDP' in descriptions
    assert 'TP' in descriptions
    assert 'FO' in descriptions
    assert 'UO' in descriptions
    
    assert descriptions['G'] == 'Ground out'
    assert descriptions['L'] == 'Line out'
    assert descriptions['F'] == 'Fly out'
    assert descriptions['P'] == 'Pop out'
    assert descriptions['B'] == 'Bunt out'
    assert descriptions['SF'] == 'Sacrifice fly'
    assert descriptions['SH'] == 'Sacrifice hit/bunt'
    assert descriptions['GDP'] == 'Grounded into double play'
    assert descriptions['LDP'] == 'Lined into double play'
    assert descriptions['TP'] == 'Triple play'
    assert descriptions['FO'] == 'Force out'
    assert descriptions['UO'] == 'Unassisted out' 