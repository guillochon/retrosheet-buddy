from pathlib import Path

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def _make_editor(tmp_path: Path) -> RetrosheetEditor:
    event_file = EventFile(games=[Game(game_id="TESTPO", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)
    # Seed one empty play
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


def test_pickoff_out_sequence(tmp_path: Path):
    editor = _make_editor(tmp_path)

    # Enter pickoff detail mode and build PO2(14)
    editor._enter_detail_mode("PO")
    editor._handle_detail_mode_input("2")  # base 2
    editor._handle_detail_mode_input("1")  # pitcher
    editor._handle_detail_mode_input("4")  # second baseman
    editor._save_detail_mode_result()

    play = editor.event_file.games[0].plays[0]
    assert play.play_description == "PO2(14)"


def test_pickoff_error_no_out(tmp_path: Path):
    editor = _make_editor(tmp_path)

    # Enter pickoff detail mode and build PO1(E3)
    editor._enter_detail_mode("PO")
    editor._handle_detail_mode_input("1")  # base 1
    editor._handle_detail_mode_input("e")  # start error fielder select
    editor._handle_detail_mode_input("3")  # error on 1B
    editor._save_detail_mode_result()

    play = editor.event_file.games[0].plays[0]
    assert play.play_description == "PO1(E3)"


def test_pickoff_caught_stealing_sequence(tmp_path: Path):
    editor = _make_editor(tmp_path)

    # Enter POCS detail mode and build POCS2(1361)
    editor._enter_detail_mode("POCS")
    editor._handle_detail_mode_input("2")  # base 2
    for k in ["1", "3", "6", "1"]:
        editor._handle_detail_mode_input(k)
    editor._save_detail_mode_result()

    play = editor.event_file.games[0].plays[0]
    assert play.play_description == "POCS2(1361)"
