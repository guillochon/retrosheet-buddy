from pathlib import Path

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def _make_editor(tmp_path: Path) -> RetrosheetEditor:
    event_file = EventFile(games=[Game(game_id="TESTBR", info=GameInfo())])
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


def test_balk_multiple_advances(tmp_path: Path):
    editor = _make_editor(tmp_path)

    editor._enter_detail_mode("BK")
    # 3 -> H, then 1 -> 2
    editor._handle_detail_mode_input("3")
    editor._handle_detail_mode_input("4")  # home
    editor._handle_detail_mode_input("1")
    editor._handle_detail_mode_input("2")
    editor._save_detail_mode_result()

    play = editor.event_file.games[0].plays[0]
    assert play.play_description == "BK.3-H;1-2"


def test_defensive_indifference_simple(tmp_path: Path):
    editor = _make_editor(tmp_path)

    editor._enter_detail_mode("DI")
    editor._handle_detail_mode_input("1")
    editor._handle_detail_mode_input("2")
    editor._save_detail_mode_result()

    play = editor.event_file.games[0].plays[0]
    assert play.play_description == "DI.1-2"


def test_passed_ball_and_wild_pitch(tmp_path: Path):
    # PB single advance
    editor_pb = _make_editor(tmp_path)
    editor_pb._enter_detail_mode("PB")
    editor_pb._handle_detail_mode_input("2")
    editor_pb._handle_detail_mode_input("3")
    editor_pb._save_detail_mode_result()
    play_pb = editor_pb.event_file.games[0].plays[0]
    assert play_pb.play_description == "PB.2-3"

    # WP multiple advances
    editor_wp = _make_editor(tmp_path)
    editor_wp._enter_detail_mode("WP")
    editor_wp._handle_detail_mode_input("2")
    editor_wp._handle_detail_mode_input("3")
    editor_wp._handle_detail_mode_input("1")
    editor_wp._handle_detail_mode_input("2")
    editor_wp._save_detail_mode_result()
    play_wp = editor_wp.event_file.games[0].plays[0]
    assert play_wp.play_description == "WP.2-3;1-2"


def test_stolen_base_single_and_double(tmp_path: Path):
    # Single stolen base SB2
    editor_sb_single = _make_editor(tmp_path)
    editor_sb_single._enter_detail_mode("SB")
    editor_sb_single._handle_detail_mode_input("2")
    editor_sb_single._save_detail_mode_result()
    play_sb_single = editor_sb_single.event_file.games[0].plays[0]
    assert play_sb_single.play_description == "SB2"

    # Double steal second and third -> ordered as SB2;SB3
    editor_sb_double = _make_editor(tmp_path)
    editor_sb_double._enter_detail_mode("SB")
    editor_sb_double._handle_detail_mode_input("2")
    editor_sb_double._handle_detail_mode_input("3")
    editor_sb_double._save_detail_mode_result()
    play_sb_double = editor_sb_double.event_file.games[0].plays[0]
    assert play_sb_double.play_description == "SB2;SB3"

    # Second and home
    editor_sb_home = _make_editor(tmp_path)
    editor_sb_home._enter_detail_mode("SB")
    editor_sb_home._handle_detail_mode_input("2")
    editor_sb_home._handle_detail_mode_input("4")  # home
    editor_sb_home._save_detail_mode_result()
    play_sb_home = editor_sb_home.event_file.games[0].plays[0]
    assert play_sb_home.play_description == "SB2;SBH"


def test_out_advancing_simple_and_out_with_fielders(tmp_path: Path):
    # Simple advance OA.2-3
    editor_oa_adv = _make_editor(tmp_path)
    editor_oa_adv._enter_detail_mode("OA")
    editor_oa_adv._handle_detail_mode_input("2")  # choose runner at 2B
    editor_oa_adv._handle_detail_mode_input("-")  # choose advance action
    editor_oa_adv._handle_detail_mode_input("3")  # destination
    editor_oa_adv._save_detail_mode_result()
    play_oa_adv = editor_oa_adv.event_file.games[0].plays[0]
    assert play_oa_adv.play_description == "OA.2-3"

    # Out attempting to advance with fielders OA.2X3(25)
    editor_oa_out = _make_editor(tmp_path)
    editor_oa_out._enter_detail_mode("OA")
    editor_oa_out._handle_detail_mode_input("2")  # runner at 2B
    editor_oa_out._handle_detail_mode_input("x")  # out action
    editor_oa_out._handle_detail_mode_input("3")  # out at 3B
    # fielder sequence (2 then 5), then ENTER to finalize the token before saving
    editor_oa_out._handle_detail_mode_input("2")
    editor_oa_out._handle_detail_mode_input("5")
    editor_oa_out._handle_detail_mode_input("\r")
    editor_oa_out._save_detail_mode_result()
    play_oa_out = editor_oa_out.event_file.games[0].plays[0]
    assert play_oa_out.play_description == "OA.2X3(25)"
