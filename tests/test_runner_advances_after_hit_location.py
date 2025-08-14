from pathlib import Path

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def _make_editor(tmp_path: Path) -> RetrosheetEditor:
    event_file = EventFile(games=[Game(game_id="TESTRUN", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)
    event_file.games[0].plays.append(
        Play(
            inning=1,
            team=0,
            batter_id="bat0001",
            count="00",
            pitches="",
            play_description="",
        )
    )
    editor.current_game_index = 0
    editor.current_play_index = 0
    return editor


def test_advance_runner_after_hit_location_single(tmp_path: Path):
    editor = _make_editor(tmp_path)

    # Enter a single with ground ball to shortstop
    editor._enter_detail_mode("S")
    editor._handle_detail_mode_input("g")
    editor._handle_detail_mode_input("6")

    # Auto-open Hit Location builder; choose a simple location and apply
    # Choose position digit and press ENTER
    editor._handle_modifier_mode_input("h")  # ensure we're in hit location group
    editor._handle_modifier_mode_input("7")
    editor._handle_modifier_mode_input("\r")

    # Now open Advance Runner builder and add a 2-3 advance, press ENTER to apply
    editor._handle_modifier_mode_input("r")
    editor._handle_modifier_mode_input("2")
    editor._handle_modifier_mode_input("3")
    editor._handle_modifier_mode_input("\r")

    play = editor.event_file.games[0].plays[0]
    assert ".2-3" in play.play_description


def test_advance_runner_multiple_tokens_appended_with_semicolons(tmp_path: Path):
    editor = _make_editor(tmp_path)

    # Enter a double with line drive to left
    editor._enter_detail_mode("D")
    editor._handle_detail_mode_input("l")
    editor._handle_detail_mode_input("7")

    # Apply a hit location quickly
    editor._handle_modifier_mode_input("h")
    editor._handle_modifier_mode_input("7")
    editor._handle_modifier_mode_input("\r")

    # First advance 2-3
    editor._handle_modifier_mode_input("r")
    editor._handle_modifier_mode_input("2")
    editor._handle_modifier_mode_input("3")
    editor._handle_modifier_mode_input("\r")

    # Second advance 1-2
    editor._handle_modifier_mode_input("r")
    editor._handle_modifier_mode_input("1")
    editor._handle_modifier_mode_input("2")
    editor._handle_modifier_mode_input("\r")

    play = editor.event_file.games[0].plays[0]
    # Ensure both advances present and ordered as appended
    assert ".2-3;1-2" in play.play_description or ".1-2;2-3" in play.play_description
