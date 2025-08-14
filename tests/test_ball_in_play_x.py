"""Tests for appending 'X' to pitch strings when ball is put in play,
and for the pitch-mode shortcut to mark ball in play and switch modes.
"""

from pathlib import Path

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def make_editor(tmp_path: Path) -> RetrosheetEditor:
    test_game = Game(
        game_id="TESTX01",
        info=GameInfo(date="2024-01-01", home_team="HOME", away_team="AWAY"),
        players=[],
        plays=[
            Play(
                inning=1,
                team=0,
                batter_id="BAT1",
                count="00",
                pitches="",
                play_description="",
            ),
            Play(
                inning=1,
                team=0,
                batter_id="BAT2",
                count="00",
                pitches="",
                play_description="",
            ),
        ],
    )
    test_event_file = EventFile(games=[test_game])
    return RetrosheetEditor(test_event_file, tmp_path)


def test_pitch_mode_ball_in_play_shortcut_adds_x_and_switches_mode(tmp_path: Path):
    editor = make_editor(tmp_path)

    assert editor.mode == "pitch"
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.pitches == ""

    # Use the internal helper directly to simulate the '.' shortcut
    editor._mark_ball_in_play_and_switch()

    assert current_play.pitches == "X"
    assert editor.mode == "play"


def test_append_x_when_saving_hit_in_play(tmp_path: Path):
    editor = make_editor(tmp_path)
    editor.current_play_index = 0

    # Enter detail mode for a Single
    editor._enter_detail_mode("S")
    # Choose hit type (Grounder) and a fielder (8 for CF)
    editor.detail_mode_hit_type = "G"
    editor.detail_mode_fielders = [8]
    editor._save_detail_mode_result()

    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.startswith("S8/G")
    assert current_play.pitches == "X"


def test_append_x_when_saving_out_in_play(tmp_path: Path):
    editor = make_editor(tmp_path)
    editor.current_play_index = 1

    # Enter detail mode for a generic OUT -> choose out type Ground out and fielder 6
    editor._enter_detail_mode("OUT")
    editor.detail_mode_out_type = "G"
    editor.detail_mode_fielders = [6]
    editor._save_detail_mode_result()

    current_play = editor.event_file.games[0].plays[1]
    assert current_play.play_description.startswith(
        "6/G"
    ) or current_play.play_description.startswith("G6")
    assert current_play.pitches == "X"
