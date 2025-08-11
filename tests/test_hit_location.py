from pathlib import Path

from retrosheet_buddy.editor import RetrosheetEditor
from retrosheet_buddy.models import EventFile, Game, GameInfo, Play


def _make_editor_with_play(tmp_path: Path) -> RetrosheetEditor:
    event_file = EventFile(games=[Game(game_id="TEST", info=GameInfo())])
    editor = RetrosheetEditor(event_file, tmp_path)
    test_game = event_file.games[0]
    test_game.plays.append(Play(
        inning=1, team=0, batter_id="test0001",
        count="00", pitches="", play_description=""
    ))
    return editor


def _save_single_to_shortstop(editor: RetrosheetEditor) -> None:
    # Enter detail mode and record a single, grounder to shortstop (S6/G6)
    editor._enter_detail_mode('S')
    editor._handle_detail_mode_input('g')  # grounder
    editor._handle_detail_mode_input('6')  # shortstop
    editor._save_detail_mode_result()


def _enter_hit_location_builder(editor: RetrosheetEditor) -> None:
    # Enter modifiers selection UI and select Hit Location group
    editor.mode = 'detail'
    editor._start_modifier_detail_mode()
    editor._handle_modifier_mode_input('h')


def test_hit_location_append_no_separator_on_hit(tmp_path: Path):
    editor = _make_editor_with_play(tmp_path)
    _save_single_to_shortstop(editor)

    # Now append hit location 89D and ensure no slash or space is inserted
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('9')
    editor._handle_modifier_mode_input('d')
    editor._handle_modifier_mode_input('\r')  # apply builder

    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G689D')

    # Finish modifiers
    editor._handle_modifier_mode_input('\r')
    assert editor.mode == 'pitch'


def test_hit_location_L_only_for_exact_7_or_9(tmp_path: Path):
    editor = _make_editor_with_play(tmp_path)
    _save_single_to_shortstop(editor)

    # Exact 7 should allow L
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('7')
    editor._handle_modifier_mode_input('l')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G67L')

    # Finish modifiers
    editor._handle_modifier_mode_input('\r')

    # 78 should NOT allow L (remains without L)
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('7')
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('l')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G67L78')

    # Finish modifiers
    editor._handle_modifier_mode_input('\r')


def test_hit_location_M_only_for_4_or_6(tmp_path: Path):
    editor = _make_editor_with_play(tmp_path)
    _save_single_to_shortstop(editor)

    # 6 should allow M
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('6')
    editor._handle_modifier_mode_input('m')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G66M')
    editor._handle_modifier_mode_input('\r')

    # 5 should NOT allow M
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('5')
    editor._handle_modifier_mode_input('m')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G66M5')
    editor._handle_modifier_mode_input('\r')


def test_hit_location_depth_variants(tmp_path: Path):
    editor = _make_editor_with_play(tmp_path)
    _save_single_to_shortstop(editor)

    # Shallow
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('s')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G68S')
    editor._handle_modifier_mode_input('\r')

    # Normal (no depth letter)
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('n')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G68S8')
    editor._handle_modifier_mode_input('\r')

    # Deep
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('d')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G68S88D')
    editor._handle_modifier_mode_input('\r')

    # Extra Deep (XD)
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('x')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G68S88D8XD')
    editor._handle_modifier_mode_input('\r')


def test_hit_location_F_toggle_only_for_specific_positions(tmp_path: Path):
    editor = _make_editor_with_play(tmp_path)
    _save_single_to_shortstop(editor)

    # 7 allows F
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('7')
    editor._handle_modifier_mode_input('f')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G67F')
    editor._handle_modifier_mode_input('\r')

    # 8 does not allow F; pressing f should have no effect
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('8')
    editor._handle_modifier_mode_input('f')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G67F8')
    editor._handle_modifier_mode_input('\r')

    # 23 allows F
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('2')
    editor._handle_modifier_mode_input('3')
    editor._handle_modifier_mode_input('f')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G67F823F')
    editor._handle_modifier_mode_input('\r')

    # 25 allows F
    _enter_hit_location_builder(editor)
    editor._handle_modifier_mode_input('2')
    editor._handle_modifier_mode_input('5')
    editor._handle_modifier_mode_input('f')
    editor._handle_modifier_mode_input('\r')
    current_play = editor.event_file.games[0].plays[0]
    assert current_play.play_description.endswith('S6/G67F823F25F')
    editor._handle_modifier_mode_input('\r')

