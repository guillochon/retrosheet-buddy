"""Test sacrifice fly and sacrifice hit functionality."""

import tempfile
from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def test_sacrifice_fly_shortcut():
    """Test that 'f' key maps to SF (sacrifice fly)."""
    # Create a minimal event file
    event_file = EventFile()
    game = Game(game_id="TEST", info=GameInfo())
    game.plays = [
        Play(
            inning=1,
            team=0,
            batter_id="test001",
            count="00",
            pitches="",
            play_description="",
        )
    ]
    event_file.games = [game]

    with tempfile.TemporaryDirectory() as temp_dir:
        editor = RetrosheetEditor(event_file, Path(temp_dir))

        # Test that 'f' maps to 'SF' in play_hotkeys
        assert "f" in editor.play_hotkeys
        assert editor.play_hotkeys["f"] == "SF"


def test_sacrifice_hit_shortcut():
    """Test that 'k' key maps to SH (sacrifice hit/bunt)."""
    # Create a minimal event file
    event_file = EventFile()
    game = Game(game_id="TEST", info=GameInfo())
    game.plays = [
        Play(
            inning=1,
            team=0,
            batter_id="test001",
            count="00",
            pitches="",
            play_description="",
        )
    ]
    event_file.games = [game]

    with tempfile.TemporaryDirectory() as temp_dir:
        editor = RetrosheetEditor(event_file, Path(temp_dir))

        # Test that 'k' maps to 'SH' in play_hotkeys
        assert "k" in editor.play_hotkeys
        assert editor.play_hotkeys["k"] == "SH"


def test_sf_sh_enter_detail_mode():
    """Test that SF and SH enter detail mode when selected."""
    # Create a minimal event file
    event_file = EventFile()
    game = Game(game_id="TEST", info=GameInfo())
    game.plays = [
        Play(
            inning=1,
            team=0,
            batter_id="test001",
            count="00",
            pitches="",
            play_description="",
        )
    ]
    event_file.games = [game]

    with tempfile.TemporaryDirectory() as temp_dir:
        editor = RetrosheetEditor(event_file, Path(temp_dir))

        # Test SF enters detail mode
        editor.mode = "play"
        editor._enter_detail_mode("SF")
        assert editor.mode == "detail"
        assert editor.detail_mode_result == "SF"

        # Reset and test SH enters detail mode
        editor.mode = "play"
        editor._enter_detail_mode("SH")
        assert editor.mode == "detail"
        assert editor.detail_mode_result == "SH"


def test_sf_sh_in_play_descriptions():
    """Test that SF and SH are included in play descriptions."""
    # Create a minimal event file
    event_file = EventFile()
    game = Game(game_id="TEST", info=GameInfo())
    game.plays = [
        Play(
            inning=1,
            team=0,
            batter_id="test001",
            count="00",
            pitches="",
            play_description="",
        )
    ]
    event_file.games = [game]

    with tempfile.TemporaryDirectory() as temp_dir:
        editor = RetrosheetEditor(event_file, Path(temp_dir))

        descriptions = editor._get_play_descriptions()
        assert "SF" in descriptions
        assert "SH" in descriptions
        assert descriptions["SF"] == "Sacrifice fly"
        assert descriptions["SH"] == "Sacrifice hit/bunt"


def test_sf_sh_generate_detailed_description():
    """Test that SF and SH generate proper detailed play descriptions."""
    # Create a minimal event file
    event_file = EventFile()
    game = Game(game_id="TEST", info=GameInfo())
    game.plays = [
        Play(
            inning=1,
            team=0,
            batter_id="test001",
            count="00",
            pitches="",
            play_description="",
        )
    ]
    event_file.games = [game]

    with tempfile.TemporaryDirectory() as temp_dir:
        editor = RetrosheetEditor(event_file, Path(temp_dir))

        # Test SF with fielding position
        sf_description = editor._generate_detailed_play_description("SF", "F", 7)
        assert sf_description == "SF7/F"

        # Test SF without fielding position
        sf_description_no_pos = editor._generate_detailed_play_description("SF", "F", 0)
        assert sf_description_no_pos == "SF/F"

        # Test SH with fielding position
        sh_description = editor._generate_detailed_play_description("SH", "B", 3)
        assert sh_description == "SH3/B"

        # Test SH without fielding position
        sh_description_no_pos = editor._generate_detailed_play_description("SH", "B", 0)
        assert sh_description_no_pos == "SH/B"
