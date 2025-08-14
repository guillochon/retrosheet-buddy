"""Test next incomplete play functionality."""

from pathlib import Path

import pytest

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


@pytest.fixture
def test_event_file_mixed():
    """Create a test event file with mixed complete and incomplete plays."""
    game_info = GameInfo(
        date="2023-04-01", game_id="TEST202304010", home_team="HOME", away_team="AWAY"
    )

    plays = [
        # Complete play
        Play(
            inning=1,
            team=0,
            batter_id="TEST0001",
            count="32",
            pitches="BBSFS",
            play_description="S6/G",
        ),
        # Incomplete - no pitches
        Play(
            inning=1,
            team=0,
            batter_id="TEST0002",
            count="12",
            pitches="",
            play_description="K",
        ),
        # Complete play
        Play(
            inning=1,
            team=1,
            batter_id="TEST0003",
            count="21",
            pitches="BCB",
            play_description="W",
        ),
        # Incomplete - no play description
        Play(
            inning=2,
            team=0,
            batter_id="TEST0004",
            count="23",
            pitches="BBSF",
            play_description="",
        ),
        # Incomplete - count is ??
        Play(
            inning=2,
            team=0,
            batter_id="TEST0005",
            count="??",
            pitches="BBF",
            play_description="W",
        ),
        # Complete play
        Play(
            inning=2,
            team=1,
            batter_id="TEST0006",
            count="01",
            pitches="BF",
            play_description="HR",
        ),
    ]

    game = Game(game_id="TEST202304010", info=game_info, plays=plays)

    return EventFile(games=[game])


@pytest.fixture
def test_event_file_all_complete():
    """Create a test event file with all complete plays."""
    game_info = GameInfo(
        date="2023-04-01", game_id="TEST202304010", home_team="HOME", away_team="AWAY"
    )

    plays = [
        Play(
            inning=1,
            team=0,
            batter_id="TEST0001",
            count="32",
            pitches="BBSFS",
            play_description="S6/G",
        ),
        Play(
            inning=1,
            team=0,
            batter_id="TEST0002",
            count="12",
            pitches="BSF",
            play_description="K",
        ),
        Play(
            inning=1,
            team=1,
            batter_id="TEST0003",
            count="21",
            pitches="BCB",
            play_description="W",
        ),
    ]

    game = Game(game_id="TEST202304010", info=game_info, plays=plays)

    return EventFile(games=[game])


def test_next_incomplete_play_finds_next(test_event_file_mixed, tmp_path):
    """Test that next incomplete play finds the next incomplete play."""
    editor = RetrosheetEditor(test_event_file_mixed, tmp_path)

    # Start at play 0 (complete)
    assert editor.current_play_index == 0

    # Jump to next incomplete (should go to play 1 - no pitches)
    editor._next_incomplete_play()
    assert editor.current_play_index == 1


def test_next_incomplete_play_skips_complete(test_event_file_mixed, tmp_path):
    """Test that next incomplete play skips complete plays."""
    editor = RetrosheetEditor(test_event_file_mixed, tmp_path)

    # Start at play 1 (incomplete - no pitches)
    editor.current_play_index = 1

    # Jump to next incomplete (should skip play 2 which is complete and go to play 3 - no play description)
    editor._next_incomplete_play()
    assert editor.current_play_index == 3


def test_next_incomplete_play_wraps_around(test_event_file_mixed, tmp_path):
    """Test that next incomplete play wraps around to beginning."""
    editor = RetrosheetEditor(test_event_file_mixed, tmp_path)

    # Start at play 5 (complete - last play)
    editor.current_play_index = 5

    # Jump to next incomplete (should wrap around and go to play 1 - no pitches)
    editor._next_incomplete_play()
    assert editor.current_play_index == 1


def test_next_incomplete_play_detects_unknown_count(test_event_file_mixed, tmp_path):
    """Test that next incomplete play detects ?? count."""
    editor = RetrosheetEditor(test_event_file_mixed, tmp_path)

    # Start at play 3 (incomplete - no play description)
    editor.current_play_index = 3

    # Jump to next incomplete (should go to play 4 - ?? count)
    editor._next_incomplete_play()
    assert editor.current_play_index == 4


def test_next_incomplete_play_no_incomplete_plays(
    test_event_file_all_complete, tmp_path
):
    """Test that next incomplete play stays in place when all plays are complete."""
    editor = RetrosheetEditor(test_event_file_all_complete, tmp_path)

    # Start at play 0
    assert editor.current_play_index == 0

    # Jump to next incomplete (should stay at play 0 since all are complete)
    editor._next_incomplete_play()
    assert editor.current_play_index == 0


def test_next_incomplete_play_no_games(tmp_path):
    """Test that next incomplete play handles empty games gracefully."""
    empty_event_file = EventFile(games=[])
    editor = RetrosheetEditor(empty_event_file, tmp_path)

    # This should not crash and should return early
    editor._next_incomplete_play()


def test_next_incomplete_play_no_plays(tmp_path):
    """Test that next incomplete play handles games with no plays gracefully."""
    game_info = GameInfo(
        date="2023-04-01", game_id="TEST202304010", home_team="HOME", away_team="AWAY"
    )

    game = Game(game_id="TEST202304010", info=game_info, plays=[])
    event_file = EventFile(games=[game])
    editor = RetrosheetEditor(event_file, tmp_path)

    # This should return early without crashing
    editor._next_incomplete_play()

    # Should remain at play 0 (even though there are no plays)
    assert editor.current_play_index == 0


def test_next_incomplete_play_original_count_unknown(tmp_path):
    """Test that next incomplete play detects original_count being ??."""
    game_info = GameInfo(
        date="2023-04-01", game_id="TEST202304010", home_team="HOME", away_team="AWAY"
    )

    plays = [
        # Complete play
        Play(
            inning=1,
            team=0,
            batter_id="TEST0001",
            count="32",
            original_count="32",
            pitches="BBSFS",
            play_description="S6/G",
        ),
        # Incomplete - original_count is ??
        Play(
            inning=1,
            team=0,
            batter_id="TEST0002",
            count="12",
            original_count="??",
            pitches="BSF",
            play_description="K",
        ),
    ]

    game = Game(game_id="TEST202304010", info=game_info, plays=plays)
    event_file = EventFile(games=[game])
    editor = RetrosheetEditor(event_file, tmp_path)

    # Start at play 0 (complete)
    assert editor.current_play_index == 0

    # Jump to next incomplete (should go to play 1 - original_count is ??)
    editor._next_incomplete_play()
    assert editor.current_play_index == 1


def test_next_incomplete_play_mode_adjustment(test_event_file_mixed, tmp_path):
    """Test that next incomplete play properly adjusts mode after navigation."""
    editor = RetrosheetEditor(test_event_file_mixed, tmp_path)

    # Start at play 0 in pitch mode
    editor.mode = "pitch"
    assert editor.current_play_index == 0

    # Jump to next incomplete (play 1 - no pitches)
    editor._next_incomplete_play()

    # Should be at play 1 and mode should be adjusted appropriately
    assert editor.current_play_index == 1
    # Mode adjustment logic is tested in _auto_set_mode_after_navigation


def test_next_incomplete_play_finds_current_if_incomplete(
    test_event_file_mixed, tmp_path
):
    """Test that next incomplete play can find current play if it's incomplete and no others are."""
    editor = RetrosheetEditor(test_event_file_mixed, tmp_path)

    # Start at play 1 (incomplete - no pitches) but imagine all other plays are now complete
    editor.current_play_index = 1

    # Temporarily make all other plays complete to test wrap-around to current
    current_game = editor.event_file.games[0]
    # Save original states
    original_pitches = []
    original_descriptions = []
    original_counts = []

    for i, play in enumerate(current_game.plays):
        original_pitches.append(play.pitches)
        original_descriptions.append(play.play_description)
        original_counts.append(play.count)

        if i != 1:  # Don't modify play 1 (current position)
            play.pitches = "BSF"
            play.play_description = "K"
            play.count = "12"

    # Jump to next incomplete (should wrap around and come back to play 1)
    editor._next_incomplete_play()
    assert editor.current_play_index == 1

    # Restore original states
    for i, play in enumerate(current_game.plays):
        play.pitches = original_pitches[i]
        play.play_description = original_descriptions[i]
        play.count = original_counts[i]
