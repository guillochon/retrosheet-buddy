"""Interactive editor for Retrosheet event files."""

import platform
import re
import sys
from pathlib import Path
from typing import List, Tuple

import click
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .constants import (
    DETAIL_MODE_SHORTCUTS,
    FIELDING_POSITION_DESCRIPTIONS,
    FIELDING_POSITION_HOTKEYS,
    HIT_TYPE_DESCRIPTIONS,
    HIT_TYPE_HOTKEYS,
    MODIFIER_DESCRIPTIONS,
    MODIFIER_GROUPS,
    NAVIGATION_SHORTCUTS,
    OUT_TYPE_DESCRIPTIONS,
    OUT_TYPE_HOTKEYS,
    PITCH_DESCRIPTIONS,
    PITCH_HOTKEYS,
    PITCH_SHORTCUTS,
    PLAY_DESCRIPTIONS,
    PLAY_HOTKEYS,
    PLAY_SHORTCUTS,
)
from .models import EventFile, Game, Play
from .parser import parse_event_file
from .writer import write_event_file


def validate_shortcuts() -> None:
    """
    Validate that no navigation shortcuts conflict with mode shortcuts.

    The application uses a mode-based system where:
    - Navigation shortcuts work in all modes
    - Mode shortcuts only work in their specific mode
    - Detail mode shortcuts only work in detail mode

    Raises:
        ValueError: If any conflicts are found between navigation and mode shortcuts.
    """
    # Check for conflicts between navigation and mode shortcuts
    conflicts: List[Tuple[str, str, str, str]] = []

    # Check navigation vs pitch mode conflicts
    for key in NAVIGATION_SHORTCUTS:
        if key in PITCH_SHORTCUTS:
            conflicts.append(
                (
                    key,
                    NAVIGATION_SHORTCUTS[key],
                    "navigation",
                    f"pitch mode: {PITCH_SHORTCUTS[key]}",
                )
            )

    # Check navigation vs play mode conflicts
    for key in NAVIGATION_SHORTCUTS:
        if key in PLAY_SHORTCUTS:
            conflicts.append(
                (
                    key,
                    NAVIGATION_SHORTCUTS[key],
                    "navigation",
                    f"play mode: {PLAY_SHORTCUTS[key]}",
                )
            )

    # Check navigation vs detail mode conflicts
    for key in NAVIGATION_SHORTCUTS:
        if key in DETAIL_MODE_SHORTCUTS:
            conflicts.append(
                (
                    key,
                    NAVIGATION_SHORTCUTS[key],
                    "navigation",
                    f"detail mode: {DETAIL_MODE_SHORTCUTS[key]}",
                )
            )

    # Remove duplicate conflicts (same key appearing in multiple comparisons)
    unique_conflicts = []
    seen_keys = set()
    for conflict in conflicts:
        if conflict[0] not in seen_keys:
            unique_conflicts.append(conflict)
            seen_keys.add(conflict[0])

    if unique_conflicts:
        error_message = "CRITICAL: Navigation shortcut conflicts detected!\n\n"
        for key, action1, context1, action2 in unique_conflicts:
            error_message += f"  Key '{key}' conflicts:\n"
            error_message += f"    - {context1}: {action1}\n"
            error_message += f"    - {action2}\n\n"

        error_message += (
            "Navigation shortcuts must have exclusive access to their keys.\n"
        )
        error_message += (
            "Please reassign conflicting mode shortcuts to different keys.\n"
        )
        error_message += (
            "All conflicts must be resolved for proper editor functionality."
        )

        raise ValueError(error_message)


def get_key() -> str:
    """Get a single key press without requiring Enter."""
    if platform.system() == "Windows":
        import msvcrt

        key = msvcrt.getch()
        if key == b"\xe0":  # Extended key
            key = msvcrt.getch()
            if key == b"H":
                return "up"
            elif key == b"P":
                return "down"
            elif key == b"K":
                return "left"
            elif key == b"M":
                return "right"
        decoded_key = key.decode("utf-8", errors="ignore")
        # Handle TAB key
        if decoded_key == "\t":
            return "tab"
        return decoded_key.lower()
    else:
        # Unix-like systems
        import termios
        import tty

        try:
            # Save terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)

            try:
                # Set terminal to raw mode
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)

                # Handle special keys
                if ch == "\x1b":  # Escape sequence
                    next_ch = sys.stdin.read(1)
                    if next_ch == "[":
                        third_ch = sys.stdin.read(1)
                        if third_ch == "A":
                            return "up"
                        elif third_ch == "B":
                            return "down"
                        elif third_ch == "C":
                            return "right"
                        elif third_ch == "D":
                            return "left"

                # Handle TAB key
                if ch == "\t":
                    return "tab"

                return ch.lower()

            finally:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (termios.error, OSError):
            # Fallback for non-TTY environments
            return input().lower()


class RetrosheetEditor:
    """Interactive editor for Retrosheet event files."""

    def __init__(self, event_file: EventFile, output_dir: Path):
        self.event_file = event_file
        self.output_dir = output_dir
        self.console = Console()
        self.current_game_index = 0
        self.current_play_index = 0
        self.mode = "pitch"  # 'pitch', 'play', or 'detail'

        # Detail mode state
        self.detail_mode_result = (
            None  # The play result selected before entering detail mode
        )
        self.detail_mode_hit_type = None  # G, L, F, etc.
        self.detail_mode_fielders = []  # List of fielders for multi-fielder plays (1-9)
        self.detail_mode_out_type = None  # OUT, GDP, LDP, TP, etc.
        self.detail_mode_runner_outs = (
            []
        )  # List of runner outs for force plays, DPs, etc.

        # Additional (auxiliary) detail selection state
        self.modifier_selection_active = (
            False  # When True, detail mode shows additional detail groups/options
        )
        self.selected_modifier_group = None  # Currently selected group key
        self.selected_modifiers = (
            []
        )  # Collected modifier codes to append (e.g., ["AP", "MREV"])
        self.modifier_param_request = None  # e.g., { 'code': 'E$', 'type': 'fielder' } or { 'code': 'TH%', 'type': 'base' }
        self.current_modifier_options_keymap = (
            {}
        )  # map single-letter key -> modifier code for current group view
        self.modifiers_live_applied = (
            False  # If True, modifiers are applied immediately upon selection
        )
        # Reference modifier groups and descriptions from constants
        self.modifier_descriptions = MODIFIER_DESCRIPTIONS
        self.modifier_groups = MODIFIER_GROUPS

        # Hit Location builder state (used within modifier selection UI)
        self.hit_location_active = False
        self.hit_location_positions = ""  # one or two digits 1-9
        self.hit_location_suffix = ""  # '' or 'M' or 'L'
        self.hit_location_depth = ""  # '' | 'S' | 'D' | 'XD'
        self.hit_location_foul = False  # True to append 'F' at the end

        # Generic runner advance builder (used within modifier selection UI)
        self.advance_runner_active = False
        self.advance_runner_from_base = None  # '1','2','3' when selecting
        self.advance_runner_tokens = []  # tokens like '1-2', '2-H', '3-3'

        # Undo functionality
        self.undo_history = (
            []
        )  # List of (game_index, play_index, pitches, play_description) tuples

        # Reference hotkey mappings from constants
        self.pitch_hotkeys = PITCH_HOTKEYS
        self.play_hotkeys = PLAY_HOTKEYS
        self.hit_type_hotkeys = HIT_TYPE_HOTKEYS
        self.fielding_position_hotkeys = FIELDING_POSITION_HOTKEYS
        self.out_type_hotkeys = OUT_TYPE_HOTKEYS

    def run(self) -> None:
        """Run the interactive editor."""
        if not self.event_file.games:
            self.console.print("No games found in event file.", style="red")
            return

        self.console.clear()

        while True:
            try:
                self._display_interface()
                key = get_key()

                if key == "q":
                    break
                elif key == "left":
                    self._previous_play()
                elif key == "right":
                    self._next_play()
                elif key == "down":
                    self._next_incomplete_play()
                elif key == "tab":  # Switch between modes
                    if self.mode == "pitch":
                        self.mode = "play"
                    elif self.mode == "play":
                        # If current play already has a result, offer additional details
                        current_game = self.event_file.games[self.current_game_index]
                        if (
                            current_game.plays
                            and current_game.plays[
                                self.current_play_index
                            ].play_description
                        ):
                            self.mode = "detail"
                            self._start_modifier_detail_mode()
                        else:
                            self.mode = "detail"
                    elif self.mode == "detail":
                        self.mode = "pitch"  # Cycle back to pitch mode
                        self._reset_detail_mode()
                elif key == "x":  # Undo last action
                    self._undo_last_action()
                elif key == "j":  # Jump to play
                    self._jump_to_play()
                elif key == "-":  # Clear (context-sensitive)
                    if self.mode == "pitch":
                        self._clear_pitches()
                    elif self.mode == "play":
                        self._clear_play_result()
                elif self.mode == "pitch" and key in self.pitch_hotkeys:
                    code = self.pitch_hotkeys[key]
                    if code == "X":
                        # Ball in play shortcut: append 'X' to pitches and switch to play mode
                        self._mark_ball_in_play_and_switch()
                    else:
                        self._add_pitch(code)
                elif self.mode == "play" and key in self.play_hotkeys:
                    # Only certain results should enter detail mode
                    result = self.play_hotkeys[key]
                    if result == "OUT" or result in [
                        "S",
                        "D",
                        "T",
                        "HR",
                        "E",
                        "PO",
                        "POCS",
                        "CS",
                        # Base-running events that need additional detail
                        "OA",
                        "BK",
                        "DI",
                        "PB",
                        "WP",
                        "SB",
                        # Sacrifice plays that need runner advance detail
                        "SF",
                        "SH",
                    ]:
                        # Generic out requires out-type/position details
                        # Hits and errors require hit-type/position details
                        # Sacrifice plays require fielding detail and then runner advances
                        self._enter_detail_mode(result)
                    else:
                        # All other results should set immediately without entering detail mode
                        self._set_play_result(result)
                elif self.mode == "detail":
                    if self.modifier_selection_active:
                        self._handle_modifier_mode_input(key)
                    else:
                        if key == "\r" or key == "\n":  # Enter key
                            # Allow saving when out-type selected; for K, no fielder required
                            if (
                                self.detail_mode_result
                                in ["OUT", "GDP", "LDP", "TP", "FO", "UO"]
                                and self.detail_mode_out_type
                                and (
                                    self.detail_mode_fielders
                                    or self.detail_mode_out_type == "K"
                                )
                            ):
                                self._save_detail_mode_result()
                            # Allow saving hits/errors with no fielder when hit type is selected
                            elif (
                                self.detail_mode_result in ["S", "D", "T", "HR", "E"]
                                and self.detail_mode_hit_type is not None
                            ):
                                self._save_detail_mode_result()
                            # Allow saving pickoffs and caught stealing when details are selected
                            elif self.detail_mode_result in ["PO", "POCS", "CS"]:
                                self._save_detail_mode_result()
                            # Allow saving runner-advancement events (BK/DI/PB/WP/SB/OA)
                            elif self.detail_mode_result in [
                                "BK",
                                "DI",
                                "PB",
                                "WP",
                                "SB",
                                "OA",
                            ]:
                                self._save_detail_mode_result()
                        else:
                            self._handle_detail_mode_input(key)
                elif key == "\r" or key == "\n":  # Enter key
                    self._save_current_state()

            except KeyboardInterrupt:
                break

    def _display_interface(self) -> None:
        """Display the main interface."""
        self.console.clear()

        current_game = self.event_file.games[self.current_game_index]

        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="padding", size=1),
            Layout(name="header", size=3),
            Layout(name="main", size=8),
            Layout(name="controls", size=16),
        )

        # Header
        header = Panel(
            f"Game: {current_game.game_id} | "
            f"{current_game.info.away_team} @ {current_game.info.home_team} | "
            f"Date: {current_game.info.date}",
            title="Retrosheet Buddy",
            style="bold blue",
        )
        layout["header"].update(header)

        # Main content
        main_content = self._create_main_content(current_game)
        layout["main"].update(main_content)

        # Controls
        controls = self._create_controls_panel()
        layout["controls"].update(controls)

        self.console.print(layout)

    def _create_main_content(self, game: Game) -> Panel:
        """Create the main content panel."""
        if not game.plays:
            return Panel("No plays recorded yet.", title="Game Plays")

        current_play = game.plays[self.current_play_index]

        # Create table for plays
        table = Table(title=f"Play {self.current_play_index + 1} of {len(game.plays)}")
        table.add_column("Inning", style="cyan")
        table.add_column("Team", style="magenta")
        table.add_column("Batter", style="green")
        table.add_column("Count", style="yellow")
        table.add_column("Pitches", style="blue")
        table.add_column("Result", style="red")

        # Add current play with highlighting
        team_name = "Away" if current_play.team == 0 else "Home"
        batter_name = self._get_player_name(game, current_play.batter_id)

        table.add_row(
            str(current_play.inning),
            team_name,
            batter_name,
            current_play.count,
            current_play.pitches,
            current_play.play_description,
            style="bold reverse",
        )

        return Panel(table, title="Current Play")

    def _create_controls_panel(self) -> Panel:
        """Create the controls panel."""
        controls_text = Text()

        # Current mode indicator - dynamic text generation
        self._add_mode_section(controls_text)

        # Navigation - dynamic text generation
        self._add_navigation_section(controls_text)

        if self.mode == "pitch":
            # Pitch controls - generated from pitch_hotkeys dictionary
            controls_text.append("Pitch Events:\n", style="bold green")
            self._add_hotkey_controls(
                controls_text, self.pitch_hotkeys, self._get_pitch_descriptions()
            )
        elif self.mode == "play":
            # Play results - generated from play_hotkeys dictionary
            controls_text.append("Play Results:\n", style="bold red")
            self._add_hotkey_controls(
                controls_text, self.play_hotkeys, self._get_play_descriptions()
            )
        elif self.mode == "detail":
            # Detail mode controls
            controls_text.append("Detail Mode:\n", style="bold yellow")
            # Additional modifiers selection UI
            if self.modifier_selection_active:
                if self.selected_modifier_group is None:
                    controls_text.append(
                        "Add Additional Details (optional):\n", style="bold green"
                    )
                    self._add_modifier_group_controls_wrapped(controls_text)
                    if self.selected_modifiers:
                        controls_text.append(
                            f"Selected: {', '.join(self.selected_modifiers)}\n",
                            style="bold cyan",
                        )
                    controls_text.append(
                        "Press the highlighted letter to choose a group, [ENTER] to apply and exit.\n",
                        style="bold blue",
                    )
                else:
                    group_name, codes = self.modifier_groups[
                        self.selected_modifier_group
                    ]
                    controls_text.append(f"{group_name}:\n", style="bold green")
                    if self.selected_modifier_group == "h":
                        # Custom wizard UI for Hit Location
                        self._render_hit_location_builder(controls_text)
                    elif self.selected_modifier_group == "r":
                        # Advance Runner builder UI
                        if self.advance_runner_tokens:
                            controls_text.append(
                                f"Selected: {';'.join(self.advance_runner_tokens)}\n",
                                style="bold cyan",
                            )
                        if (
                            not self.advance_runner_active
                            or self.advance_runner_from_base is None
                        ):
                            controls_text.append(
                                "Select runner base: [1], [2], [3]  [ENTER] to apply, [0] back\n",
                                style="bold blue",
                            )
                        else:
                            fb = self.advance_runner_from_base
                            controls_text.append(
                                f"From base: {fb}\n", style="bold green"
                            )
                            if fb == "1":
                                controls_text.append(
                                    "Destination: [2] Second  [1] Stay (1-1)\n",
                                    style="bold blue",
                                )
                            elif fb == "2":
                                controls_text.append(
                                    "Destination: [3] Third  [2] Stay (2-2)\n",
                                    style="bold blue",
                                )
                            else:
                                controls_text.append(
                                    "Destination: [H or 4] Home  [3] Stay (3-3)\n",
                                    style="bold blue",
                                )
                            controls_text.append(
                                "[ENTER] to apply, [0] back\n", style="bold blue"
                            )
                    else:
                        # Render options in wrapped rows with max width, similar to other modes
                        self._add_modifier_options_wrapped(controls_text, codes)
                        if self.selected_modifiers:
                            controls_text.append(
                                f"Selected: {', '.join(self.selected_modifiers)}\n",
                                style="bold cyan",
                            )
                        if self.modifier_param_request:
                            if self.modifier_param_request["type"] == "fielder":
                                controls_text.append(
                                    "Enter fielder [1-9] for this modifier.\n",
                                    style="bold blue",
                                )
                            elif self.modifier_param_request["type"] == "base":
                                controls_text.append(
                                    "Enter base [1-4] for this modifier.\n",
                                    style="bold blue",
                                )
                        controls_text.append(
                            "Use letter keys to add, [0] to go back, [ENTER] to apply and exit.\n",
                            style="bold blue",
                        )
            elif self.detail_mode_result:
                controls_text.append(
                    f"Result: {self.detail_mode_result}\n", style="bold red"
                )

                # Handle different types of plays
                if self.detail_mode_result in ["OUT", "GDP", "LDP", "TP", "FO", "UO"]:
                    # Out types need out type and fielding positions (K allows optional fielders)
                    if self.detail_mode_out_type is None:
                        controls_text.append("Out Type:\n", style="bold green")
                        self._add_hotkey_controls(
                            controls_text,
                            self.out_type_hotkeys,
                            self._get_out_type_descriptions(),
                        )
                        controls_text.append(
                            "Fielding Positions: [1-9] (multiple allowed; optional for K)\n",
                            style="bold blue",
                        )
                    elif not self.detail_mode_fielders:
                        controls_text.append(
                            f"Out Type: {self.detail_mode_out_type}\n",
                            style="bold green",
                        )
                        if self.detail_mode_out_type != "K":
                            controls_text.append(
                                "Fielding Positions:\n", style="bold blue"
                            )
                            self._add_hotkey_controls(
                                controls_text,
                                self.fielding_position_hotkeys,
                                self._get_fielding_position_descriptions(),
                            )
                            controls_text.append(
                                "Select fielders sequentially (e.g., 6-4-3 for DP)\n",
                                style="bold cyan",
                            )
                            controls_text.append(
                                "Press [ENTER] when done selecting fielders\n",
                                style="bold cyan",
                            )
                        else:
                            controls_text.append(
                                "Press [ENTER] to save strikeout, or add fielders for dropped 3rd strike (e.g., K23)\n",
                                style="bold cyan",
                            )
                    else:
                        controls_text.append(
                            f"Out Type: {self.detail_mode_out_type}\n",
                            style="bold green",
                        )
                        controls_text.append(
                            f"Fielding Positions: {', '.join(map(str, self.detail_mode_fielders))}\n",
                            style="bold blue",
                        )
                        controls_text.append("Fielding Positions:\n", style="bold blue")
                        self._add_hotkey_controls(
                            controls_text,
                            self.fielding_position_hotkeys,
                            self._get_fielding_position_descriptions(),
                        )
                        controls_text.append(
                            "Press [ENTER] to save or add more positions\n",
                            style="bold cyan",
                        )
                elif self.detail_mode_result in ["PO", "POCS", "CS"]:
                    # Pickoff UI
                    if not getattr(self, "detail_pickoff_base", None):
                        if self.detail_mode_result == "PO":
                            controls_text.append(
                                "Pickoff base: [1] First  [2] Second  [3] Third\n",
                                style="bold blue",
                            )
                        else:
                            controls_text.append(
                                (
                                    "Caught stealing base: "
                                    if self.detail_mode_result == "CS"
                                    else "Pickoff-CS base: "
                                )
                                + "[2] Second  [3] Third  [H] Home (press 4 or H)\n",
                                style="bold blue",
                            )
                    else:
                        base_display = self.detail_pickoff_base
                        controls_text.append(
                            f"Base: {base_display}\n", style="bold green"
                        )
                        if self.detail_mode_result == "PO":
                            if self.detail_pickoff_error_fielder is None:
                                controls_text.append(
                                    "Fielders for putout (e.g., 13) or [E] then fielder for error (e.g., E3)\n",
                                    style="bold blue",
                                )
                            else:
                                controls_text.append(
                                    f"Error on: {self.detail_pickoff_error_fielder}\n",
                                    style="bold green",
                                )
                        else:
                            controls_text.append(
                                "Fielder sequence resulting in CS (e.g., 1361)\n",
                                style="bold blue",
                            )
                        # Show fielding position legend to aid selection
                        controls_text.append("Fielding Positions:\n", style="bold blue")
                        self._add_hotkey_controls(
                            controls_text,
                            self.fielding_position_hotkeys,
                            self._get_fielding_position_descriptions(),
                        )
                        if self.detail_pickoff_fielders:
                            controls_text.append(
                                f"Fielders: {'-'.join(map(str, self.detail_pickoff_fielders))}\n",
                                style="bold cyan",
                            )
                        controls_text.append(
                            "Press [ENTER] to save\n", style="bold cyan"
                        )
                elif self.detail_mode_result in ["BK", "DI", "PB", "WP", "SB", "OA"]:
                    # Runner advancement / stolen base / out advancing UI
                    # Show current tokens (for SB these are SB2/SB3/SBH, others are base moves like 1-2)
                    if getattr(self, "runner_tokens", None):
                        controls_text.append(
                            f"Selected: {';'.join(self.runner_tokens)}\n",
                            style="bold cyan",
                        )
                    # Per-type instructions
                    if self.detail_mode_result == "SB":
                        controls_text.append(
                            "Toggle stolen bases: [2] SB2  [3] SB3  [H or 4] SBH\n",
                            style="bold blue",
                        )
                        # Show current SB selections
                        if getattr(self, "sb_targets", None):
                            ordered = []
                            for b in ["2", "3", "H"]:
                                if b in self.sb_targets:
                                    ordered.append(f"SB{b}")
                            if ordered:
                                controls_text.append(
                                    f"Selected: {';'.join(ordered)}\n",
                                    style="bold cyan",
                                )
                        controls_text.append(
                            "Press [ENTER] to save\n", style="bold cyan"
                        )
                    elif self.detail_mode_result in ["BK", "DI", "PB", "WP"]:
                        # Simple advances only
                        current_game = self.event_file.games[self.current_game_index]
                        current_play = current_game.plays[self.current_play_index]
                        is_strikeout_recorded = bool(
                            (current_play.play_description or "").startswith("K")
                        )
                        if not getattr(self, "advance_from_base", None):
                            # Show from-base options; add Batter (B) if a strikeout is recorded
                            base_prompt = "Select runner base to advance: [1], [2], [3]"
                            if is_strikeout_recorded:
                                base_prompt += "  [B] Batter"
                            controls_text.append(base_prompt + "\n", style="bold blue")
                        else:
                            from_b = self.advance_from_base
                            from_label = "Batter" if from_b == "B" else from_b
                            controls_text.append(
                                f"From base: {from_label}\n", style="bold green"
                            )
                            if from_b == "1":
                                controls_text.append(
                                    "Destination: [2] Second\n", style="bold blue"
                                )
                            elif from_b == "2":
                                controls_text.append(
                                    "Destination: [3] Third\n", style="bold blue"
                                )
                            elif from_b == "3":
                                controls_text.append(
                                    "Destination: [H or 4] Home\n",
                                    style="bold blue",
                                )
                            elif from_b == "B":
                                controls_text.append(
                                    "Destination: [1] First  [2] Second  [3] Third  [H or 4] Home\n",
                                    style="bold blue",
                                )
                        controls_text.append(
                            "Press [ENTER] to save\n", style="bold cyan"
                        )
                    else:  # OA (can be advance or out with fielders)
                        stage = getattr(self, "oa_stage", "choose_runner")
                        if stage == "choose_runner":
                            controls_text.append(
                                "Select runner base: [1], [2], [3]\n", style="bold blue"
                            )
                        elif stage == "choose_action":
                            controls_text.append(
                                "Action: ['-' Advance]  ['X' Out attempting to advance]\n",
                                style="bold blue",
                            )
                        elif stage == "choose_dest":
                            from_b = self.oa_from_base
                            controls_text.append(
                                f"From base: {from_b}\n", style="bold green"
                            )
                            if not self.oa_out:
                                if from_b == "1":
                                    controls_text.append(
                                        "Destination: [2] Second\n", style="bold blue"
                                    )
                                elif from_b == "2":
                                    controls_text.append(
                                        "Destination: [3] Third\n", style="bold blue"
                                    )
                                else:
                                    controls_text.append(
                                        "Destination: [H or 4] Home\n",
                                        style="bold blue",
                                    )
                            else:
                                if from_b == "1":
                                    controls_text.append(
                                        "Out at: [2] Second\n", style="bold blue"
                                    )
                                elif from_b == "2":
                                    controls_text.append(
                                        "Out at: [3] Third\n", style="bold blue"
                                    )
                                else:
                                    controls_text.append(
                                        "Out at: [H or 4] Home\n", style="bold blue"
                                    )
                        elif stage == "choose_fielders":
                            controls_text.append(
                                "Enter fielder sequence digits [1-9]; press [ENTER] to finalize token\n",
                                style="bold blue",
                            )
                            if getattr(self, "oa_fielders", None):
                                controls_text.append(
                                    f"Fielders: {'-'.join(map(str, self.oa_fielders))}\n",
                                    style="bold cyan",
                                )
                        # End OA instruction rendering
                else:
                    # Regular hits need hit type and fielding position
                    if self.detail_mode_hit_type is None:
                        controls_text.append("Hit Type:\n", style="bold green")
                        self._add_hotkey_controls(
                            controls_text,
                            self.hit_type_hotkeys,
                            self._get_hit_type_descriptions(),
                        )
                        controls_text.append(
                            "Fielding Position: [1-9]\n", style="bold blue"
                        )
                    elif not self.detail_mode_fielders:
                        controls_text.append(
                            f"Hit Type: {self.detail_mode_hit_type}\n",
                            style="bold green",
                        )
                        controls_text.append("Fielding Position:\n", style="bold blue")
                        self._add_hotkey_controls(
                            controls_text,
                            self.fielding_position_hotkeys,
                            self._get_fielding_position_descriptions(),
                        )
                        controls_text.append(
                            "Press [ENTER] to save without a position\n",
                            style="bold cyan",
                        )
                    else:
                        controls_text.append(
                            f"Hit Type: {self.detail_mode_hit_type}\n",
                            style="bold green",
                        )
                        controls_text.append(
                            f"Fielding Position: {self.detail_mode_fielders[0]}\n",
                            style="bold blue",
                        )
                        controls_text.append(
                            "Press [ENTER] to save and exit detail mode.\n",
                            style="bold cyan",
                        )
            else:
                controls_text.append(
                    "Select a play result to enter detail mode.\n", style="bold red"
                )

        # Calculate the height of the generated text
        text_height = self._calculate_text_height(controls_text)

        # Add padding for panel borders and title (typically 3-4 lines)
        panel_height = text_height + 4

        return Panel(controls_text, title="Controls", height=panel_height)

    def _calculate_text_height(self, text: Text) -> int:
        """Calculate the height (number of lines) of a Text object."""
        # Convert Text to string and count lines
        text_str = str(text)
        lines = text_str.split("\n")
        # Count non-empty lines (excluding trailing empty line)
        height = len([line for line in lines if line.strip()])
        return height

    def _add_mode_section(self, controls_text: Text) -> None:
        """Add the current mode section with dynamic text generation."""
        # Calculate maximum width: minimum of console width and 120 characters
        max_width = min(self.console.width, 120)

        # Account for indentation (2 spaces)
        available_width = max_width - 2

        # Mode indicator
        mode_style = (
            "bold green"
            if self.mode == "pitch"
            else "bold red" if self.mode == "play" else "bold yellow"
        )
        controls_text.append(f"Current Mode: {self.mode.upper()}\n", style=mode_style)

        # Determine which mode TAB would switch to
        if self.mode == "pitch":
            next_mode = "play"
        elif self.mode == "play":
            next_mode = "detail"
        else:  # detail mode
            next_mode = "pitch"

        # Mode switch instruction with next mode
        mode_switch_text = f"  [TAB] Switch to {next_mode.upper()} mode"
        if len(mode_switch_text) <= available_width:
            controls_text.append(mode_switch_text + "\n\n")
        else:
            # Split if needed (though unlikely for this short text)
            controls_text.append(f"  [TAB] Switch to\n  {next_mode.upper()} mode\n\n")

    def _add_navigation_section(self, controls_text: Text) -> None:
        """Add the navigation section with dynamic text generation."""
        # Calculate maximum width: minimum of console width and 120 characters
        max_width = min(self.console.width, 120)

        # Account for indentation (2 spaces)
        available_width = max_width - 2

        controls_text.append("Navigation:\n", style="bold cyan")

        # Navigation items (use actual keys handled by get_key: left/right arrows)
        nav_items = [
            "[Left] Previous play",
            "[Right] Next play",
            "[Down] Next incomplete",
            "[J] Jump to play",
            "[Q] Quit",
            "[X] Undo last action",
        ]

        # Context-sensitive clear hint
        if self.mode == "pitch":
            nav_items.append("[-] Clear pitches")
        elif self.mode == "play":
            nav_items.append("[-] Clear result")

        current_row = []
        current_row_width = 0

        for item in nav_items:
            # Calculate width of this item plus spacing
            item_width = len(item)
            spacing_width = 2 if current_row else 0  # 2 spaces between items
            total_item_width = item_width + spacing_width

            # Check if this item fits on the current row
            if current_row_width + total_item_width <= available_width:
                current_row.append(item)
                current_row_width += total_item_width
            else:
                # Current row is full, append it and start a new row
                if current_row:
                    controls_text.append("  " + "  ".join(current_row) + "\n")
                current_row = [item]
                current_row_width = item_width

        # Append the last row if it has content
        if current_row:
            controls_text.append("  " + "  ".join(current_row) + "\n")

        controls_text.append("\n")  # Add extra spacing after navigation

    def _get_pitch_descriptions(self) -> dict:
        """Get descriptions for pitch events."""
        return PITCH_DESCRIPTIONS

    def _get_play_descriptions(self) -> dict:
        """Get descriptions for play results."""
        return PLAY_DESCRIPTIONS

    def _get_hit_type_descriptions(self) -> dict:
        """Get descriptions for hit types."""
        return HIT_TYPE_DESCRIPTIONS

    def _get_fielding_position_descriptions(self) -> dict:
        """Get descriptions for fielding positions."""
        return FIELDING_POSITION_DESCRIPTIONS

    def _get_out_type_descriptions(self) -> dict:
        """Get descriptions for out types in detail mode."""
        return OUT_TYPE_DESCRIPTIONS

    def _generate_retrosheet_play_description(
        self, result: str, fielding_position: int = 0
    ) -> str:
        """Generate proper Retrosheet play description format."""
        if result == "S":  # Single
            if fielding_position > 0:
                return f"S{fielding_position}/G"
            return "S8/G6"  # Default to center field
        elif result == "D":  # Double
            if fielding_position > 0:
                return f"D{fielding_position}/L"
            return "D7/L7"  # Default to left field
        elif result == "T":  # Triple
            if fielding_position > 0:
                return f"T{fielding_position}/L"
            return "T8/L8"  # Default to center field
        elif result == "HR":  # Home run
            return "HR/F7"  # Over left field fence
        elif result == "K":  # Strikeout
            return "K"
        elif result == "W":  # Walk
            return "W"
        elif result == "HP":  # Hit by pitch
            return "HP"
        elif result == "E":  # Error
            if fielding_position > 0:
                return f"E{fielding_position}/G"
            return "E6/G6"  # Default to shortstop
        elif result == "FC":  # Fielder's choice
            if fielding_position > 0:
                return f"FC{fielding_position}/G"
            return "FC6/G6"
        elif result == "DP":  # Double play
            return "DP/G6"
        elif result == "TP":  # Triple play
            return "TP/G6"
        elif result == "SF":  # Sacrifice fly
            if fielding_position > 0:
                return f"SF{fielding_position}/F"
            return "SF8/F8"
        elif result == "SH":  # Sacrifice bunt
            if fielding_position > 0:
                return f"SH{fielding_position}/G"
            return "SH1/G1"
        elif result == "IW":  # Intentional walk
            return "IW"
        elif result == "CI":  # Catcher interference
            return "CI"
        elif result == "OA":  # Out advancing
            return "OA"
        elif result == "ND":  # No play
            return "ND"
        # New out types
        elif result == "OUT":  # Generic out
            if fielding_position > 0:
                return f"G{fielding_position}"
            return "G6"
        elif result == "GDP":  # Grounded into double play
            if fielding_position > 0:
                return f"G{fielding_position}/GDP/G{fielding_position}"
            return "G6/GDP/G6"
        elif result == "LDP":  # Lined into double play
            if fielding_position > 0:
                return f"L{fielding_position}/LDP/L{fielding_position}"
            return "L6/LDP/L6"
        elif result == "FO":  # Force out
            if fielding_position > 0:
                return f"G{fielding_position}/FO/G{fielding_position}"
            return "G6/FO/G6"
        elif result == "UO":  # Unassisted out
            if fielding_position > 0:
                return f"G{fielding_position}/UO/G{fielding_position}"
            return "G6/UO/G6"
        else:
            return result

    def _add_hotkey_controls(
        self, controls_text: Text, hotkeys: dict, descriptions: dict
    ) -> None:
        """Add hotkey controls to the controls text."""
        # Calculate maximum width: minimum of console width and 100 characters
        max_width = min(self.console.width, 120)

        # Account for indentation (2 spaces)
        available_width = max_width - 2

        keys = list(hotkeys.keys())
        current_row = []
        current_row_width = 0

        for key in keys:
            if key in hotkeys:
                retrosheet_code = hotkeys[key]
                description = descriptions.get(retrosheet_code, retrosheet_code)
                key_entry = f"[{key.upper()}] {description}"

                # Calculate width of this entry plus spacing
                entry_width = len(key_entry)
                spacing_width = 2 if current_row else 0  # 2 spaces between entries
                total_entry_width = entry_width + spacing_width

                # Check if this entry fits on the current row
                if current_row_width + total_entry_width <= available_width:
                    current_row.append(key_entry)
                    current_row_width += total_entry_width
                else:
                    # Current row is full, append it and start a new row
                    if current_row:
                        controls_text.append("  " + "  ".join(current_row) + "\n")
                    current_row = [key_entry]
                    current_row_width = entry_width

        # Append the last row if it has content
        if current_row:
            controls_text.append("  " + "  ".join(current_row) + "\n")

    def _get_player_name(self, game: Game, player_id: str) -> str:
        """Get player name from player ID."""
        for player in game.players:
            if player.player_id == player_id:
                return player.name
        return player_id

    def _previous_play(self) -> None:
        """Go to previous play."""
        if self.current_play_index > 0:
            prior_mode = self.mode
            self.current_play_index -= 1
            self._auto_set_mode_after_navigation(prior_mode)

    def _next_play(self) -> None:
        """Go to next play."""
        current_game = self.event_file.games[self.current_game_index]
        if self.current_play_index < len(current_game.plays) - 1:
            prior_mode = self.mode
            self.current_play_index += 1
            self._auto_set_mode_after_navigation(prior_mode)

    def _jump_to_play(self) -> None:
        """Show a table of all plays and allow user to jump to a specific play."""
        if not self.event_file.games:
            return

        current_game = self.event_file.games[self.current_game_index]
        if not current_game.plays:
            return

        # Clear the screen and show the jump-to-play interface
        self.console.clear()

        # Create table of all plays
        table = Table(
            title=f"Jump to Play - {current_game.info.home_team} vs {current_game.info.away_team} ({current_game.info.date})"
        )
        table.add_column("#", style="cyan", width=4)
        table.add_column("Inning", style="magenta", width=6)
        table.add_column("Team", style="green", width=6)
        table.add_column("Batter", style="yellow", width=20)
        table.add_column("Count", style="blue", width=5)
        table.add_column("Pitches", style="red", width=15)
        table.add_column("Result", style="white", width=30)

        for i, play in enumerate(current_game.plays):
            team_name = "Away" if play.team == 0 else "Home"
            batter_name = self._get_player_name(current_game, play.batter_id)

            # Highlight current play
            style = "bold reverse" if i == self.current_play_index else None

            table.add_row(
                str(i + 1),
                str(play.inning),
                team_name,
                batter_name,
                play.count,
                play.pitches,
                play.play_description or "",
                style=style,
            )

        # Show the table
        self.console.print(table)
        self.console.print(
            "\nEnter play number (1-{}) or press any other key to cancel: ".format(
                len(current_game.plays)
            ),
            end="",
        )

        # Get user input for play number
        try:
            # Read a line of input (allow multi-digit numbers)
            user_input = input().strip()
            if user_input.isdigit():
                play_number = int(user_input)
                if 1 <= play_number <= len(current_game.plays):
                    # Valid play number - jump to it
                    prior_mode = self.mode
                    self.current_play_index = play_number - 1
                    self._auto_set_mode_after_navigation(prior_mode)
        except (ValueError, KeyboardInterrupt):
            # Invalid input or user cancelled - do nothing
            pass

        # Clear the screen and return to normal interface
        self.console.clear()

    def _next_incomplete_play(self) -> None:
        """Jump to the next play with incomplete information."""
        if not self.event_file.games:
            return

        current_game = self.event_file.games[self.current_game_index]
        if not current_game.plays:
            return

        def is_incomplete(play: Play) -> bool:
            """Check if a play has incomplete information."""
            # Check if count is ??
            if play.count == "??" or play.original_count == "??":
                return True
            # Check if pitch string is empty
            if not play.pitches:
                return True
            # Check if play description is empty
            if not play.play_description:
                return True
            return False

        # Search for the next incomplete play starting from current index + 1
        start_index = self.current_play_index + 1

        # First check from current position to end of game
        for i in range(start_index, len(current_game.plays)):
            if is_incomplete(current_game.plays[i]):
                prior_mode = self.mode
                self.current_play_index = i
                self._auto_set_mode_after_navigation(prior_mode)
                return

        # If not found, wrap around and check from beginning to current position
        for i in range(0, self.current_play_index + 1):
            if is_incomplete(current_game.plays[i]):
                prior_mode = self.mode
                self.current_play_index = i
                self._auto_set_mode_after_navigation(prior_mode)
                return

        # If no incomplete plays found, stay at current position (no-op)

    def _auto_set_mode_after_navigation(self, prior_mode: str) -> None:
        """Adjust mode after changing plays based on the new play's content.

        - If pitches are empty: switch to pitch mode
        - Else if play result is empty: switch to play mode
        - Else: keep prior mode
        """
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]

        if not (current_play.pitches or ""):
            desired_mode = "pitch"
        elif not (current_play.play_description or ""):
            desired_mode = "play"
        else:
            desired_mode = prior_mode

        if desired_mode != self.mode:
            # If leaving detail mode, clear any in-progress detail state
            if self.mode == "detail" and desired_mode in ["pitch", "play"]:
                self._reset_detail_mode()
            self.mode = desired_mode

    def _previous_game(self) -> None:
        """Go to previous game."""
        if self.current_game_index > 0:
            self.current_game_index -= 1
            self.current_play_index = 0

    def _next_game(self) -> None:
        """Go to next game."""
        if self.current_game_index < len(self.event_file.games) - 1:
            self.current_game_index += 1
            self.current_play_index = 0

    def _calculate_count(self, pitches: str, start_count: str = "00") -> str:
        """Calculate count from pitch sequence following baseball rules.

        If a non-default ``start_count`` is provided (e.g., when the prior play
        involves the same batter in the same inning), begin from that count
        instead of "00".

        Display rules:
        - Balls are capped at 3 for display
        - Strikes are capped at 2 for display
        """
        # Initialize from starting count
        try:
            start_balls = int(start_count[0]) if start_count else 0
            start_strikes = int(start_count[1]) if start_count else 0
        except (ValueError, IndexError):
            start_balls, start_strikes = 0, 0

        balls = start_balls
        strikes = start_strikes

        for pitch in pitches:
            if pitch == "B":
                balls += 1
            elif pitch in ["S", "C"]:  # Swinging strike, Called strike
                strikes += 1
            elif pitch == "F":  # Foul ball
                # Foul balls only count as strikes up to 2 strikes
                if strikes < 2:
                    strikes += 1
            elif pitch == "T":  # Foul tip
                # Foul tips count as strikes and can result in strikeout
                strikes += 1
            # Other pitch types (H, V, A, M, P, I, Q, R, E, N, O, U) don't affect count

        # Cap balls at 3 and strikes at 2 for display (never show 3 strikes)
        balls = min(balls, 3)
        strikes = min(strikes, 2)

        return f"{balls}{strikes}"

    def _calculate_raw_balls_strikes(
        self, pitches: str, start_count: str = "00"
    ) -> tuple:
        """Calculate uncapped balls and strikes from pitch sequence.

        Used for logic decisions (e.g., automatic walk/strikeout) independent of
        display capping.
        """
        try:
            start_balls = int(start_count[0]) if start_count else 0
            start_strikes = int(start_count[1]) if start_count else 0
        except (ValueError, IndexError):
            start_balls, start_strikes = 0, 0

        balls = start_balls
        strikes = start_strikes

        for pitch in pitches:
            if pitch == "B":
                balls += 1
            elif pitch in ["S", "C"]:
                strikes += 1
            elif pitch == "F":
                if strikes < 2:
                    strikes += 1
            elif pitch == "T":
                strikes += 1
            # Other pitch types (H, V, A, M, P, I, Q, R, E, N, O, U) don't affect count

        return balls, strikes

    def _starting_count_for_play_index(self, game: Game, play_index: int) -> str:
        """Return starting count for a given play index.

        If the immediately prior play involves the same batter, inning, and team,
        inherit its count; otherwise return "00".
        """
        if play_index <= 0:
            return "00"
        prior = game.plays[play_index - 1]
        current = game.plays[play_index]
        if (
            prior.inning == current.inning
            and prior.team == current.team
            and prior.batter_id == current.batter_id
        ):
            return prior.count or "00"
        return "00"

    def _has_strikeout(self, pitches: str) -> bool:
        """Return True if the pitch sequence results in a strikeout (3 strikes).

        This mirrors baseball rules:
        - S, C always add a strike
        - F adds a strike only up to 2 strikes
        - T (foul tip) adds a strike and can be strike three
        """
        strikes = 0
        for pitch in pitches:
            if pitch in ["S", "C"]:
                strikes += 1
            elif pitch == "F":
                if strikes < 2:
                    strikes += 1
            elif pitch == "T":
                strikes += 1
            # Other pitch types do not affect strikes
            if strikes >= 3:
                return True
        return False

    def _add_pitch(self, pitch: str) -> None:
        """Add a pitch to the current play."""
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]

        # Save state before making changes
        self._save_state_for_undo()

        # If a wild pitch (V) or passed ball (A) is recorded from pitch input,
        # do NOT add the V/A token to the pitch string. Only append a period to
        # separate the prior pitch sequence, then enter the runner-advancement
        # detail mode for PB/WP.
        if pitch in ["V", "A"]:
            if current_play.pitches:
                current_play.pitches += "."
            else:
                current_play.pitches = "."
            # Update count after modifying pitches
            start_count = self._starting_count_for_play_index(
                current_game, self.current_play_index
            )
            current_play.count = self._calculate_count(
                current_play.pitches, start_count
            )
            # Prepare and enter detail mode for runner advances
            self.detail_mode_from_pitch_pb_wp = True
            self.detail_mode_pb_wp_code = "WP" if pitch == "V" else "PB"
            # Save current state before switching modes
            current_play.edited = True
            self._save_current_state()
            # Enter detail mode for PB/WP
            self._enter_detail_mode(self.detail_mode_pb_wp_code)
            return

        # Add pitch to the pitch sequence (normal pitches)
        if current_play.pitches:
            current_play.pitches += pitch
        else:
            current_play.pitches = pitch

        # Update count (fouls count as strikes), inheriting prior count for same batter
        start_count = self._starting_count_for_play_index(
            current_game, self.current_play_index
        )
        current_play.count = self._calculate_count(current_play.pitches, start_count)
        # Mark as edited because pitches changed
        current_play.edited = True

        # Check for automatic walk or strikeout using RAW counts (not display-capped)
        raw_balls, raw_strikes = self._calculate_raw_balls_strikes(
            current_play.pitches, start_count
        )

        if raw_balls >= 4:
            # Automatic walk
            current_play.play_description = "W"
            # For display, show 3 balls and current strikes (capped at 2)
            display_strikes = min(raw_strikes, 2)
            current_play.count = f"3{display_strikes}"
            current_play.edited = True
            self._save_current_state()
            # Move to next batter
            self._next_play()
        elif self._has_strikeout(current_play.pitches):
            # Automatic strikeout
            # If there is already a suffix such as "+PB.2-3" from a prior PB/WP,
            # prefix the strikeout result instead of overwriting it.
            existing = current_play.play_description or ""
            if existing and not existing.startswith("K"):
                current_play.play_description = "K" + existing
            else:
                current_play.play_description = "K"
            current_play.edited = True
            self._save_current_state()
            # Do not auto-advance on strikeout
        else:
            self._save_current_state()

    def _set_play_result(self, result: str) -> None:
        """Set the result of the current play."""
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]

        # Save state before making changes
        self._save_state_for_undo()

        # Generate proper Retrosheet play description
        play_description = self._generate_retrosheet_play_description(result)
        current_play.play_description = play_description
        current_play.edited = True

        self._save_current_state()

    def _ensure_ball_in_play_marker(self) -> None:
        """Append 'X' to the pitch string if not already present and update count.

        Does not push a second undo snapshot; assumes caller already saved undo state
        for the encompassing operation.
        """
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]
        if "X" not in (current_play.pitches or ""):
            current_play.pitches = (current_play.pitches or "") + "X"
            start_count = self._starting_count_for_play_index(
                current_game, self.current_play_index
            )
            current_play.count = self._calculate_count(
                current_play.pitches, start_count
            )
            current_play.edited = True

    def _mark_ball_in_play_and_switch(self) -> None:
        """Pitch-mode shortcut: append 'X' and switch to play mode."""
        # Save state before making changes
        self._save_state_for_undo()
        self._ensure_ball_in_play_marker()
        self._save_current_state()
        self.mode = "play"

    def _save_current_state(self) -> None:
        """Save the current state to disk."""
        current_game = self.event_file.games[self.current_game_index]
        output_path = self.output_dir / f"{current_game.game_id}.EVN"

        # Create a single-game event file
        single_game_event = EventFile(games=[current_game])
        write_event_file(single_game_event, output_path)

        self.console.print(f"Saved to {output_path}", style="green")

    def _save_state_for_undo(self) -> None:
        """Save the current state for undo functionality."""
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]

        # Save current state
        state = (
            self.current_game_index,
            self.current_play_index,
            current_play.pitches,
            current_play.play_description,
        )
        self.undo_history.append(state)

        # Keep only last 10 undo states
        if len(self.undo_history) > 10:
            self.undo_history.pop(0)

    def _undo_last_action(self) -> None:
        """Undo the last action (pitch or play result)."""
        if not self.undo_history:
            self.console.print("Nothing to undo", style="yellow")
            return

        # Get the last saved state
        game_index, play_index, pitches, play_description = self.undo_history.pop()

        # Restore the state
        current_game = self.event_file.games[game_index]
        current_play = current_game.plays[play_index]

        current_play.pitches = pitches
        current_play.play_description = play_description
        # Undo restores previous state; mark as not edited relative to that state
        current_play.edited = False

        # Update count (fouls count as strikes)
        start_count = self._starting_count_for_play_index(current_game, play_index)
        current_play.count = self._calculate_count(current_play.pitches, start_count)

        self.console.print("Undo completed", style="green")
        self._save_current_state()

    def _clear_pitches(self) -> None:
        """Clear the full pitch history for the current at-bat and reset count.

        Does not modify the play result. Records an undo snapshot and saves state.
        """
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]

        # Save state before clearing
        self._save_state_for_undo()

        current_play.pitches = ""
        start_count = self._starting_count_for_play_index(
            current_game, self.current_play_index
        )
        current_play.count = self._calculate_count(current_play.pitches, start_count)
        current_play.edited = True

        self.console.print("Cleared pitches", style="green")
        self._save_current_state()

    def _clear_play_result(self) -> None:
        """Clear the result of the current play.

        Does not modify pitch history or count. Records an undo snapshot and saves state.
        """
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]

        # Save state before clearing
        self._save_state_for_undo()

        current_play.play_description = ""
        current_play.edited = True

        # If we were in detail mode workflow, ensure state is clean
        self._reset_detail_mode()

        self.console.print("Cleared play result", style="green")
        self._save_current_state()

    def _enter_detail_mode(self, result: str) -> None:
        """Enter detail mode for specifying hit type and fielding position."""
        self.detail_mode_result = result
        self.detail_mode_hit_type = None
        self.detail_mode_fielding_position = None
        self.mode = "detail"
        # Reset any previous modifier selection state so new workflows start clean
        self.modifier_selection_active = False
        self.selected_modifier_group = None
        self.selected_modifiers = []
        self.modifier_param_request = None
        self.current_modifier_options_keymap = {}
        self.modifiers_live_applied = False
        # Initialize pickoff-specific state
        self.detail_pickoff_base = None  # '1','2','3' or 'H' for home
        self.detail_pickoff_fielders = []  # list of ints 1-9
        self.detail_pickoff_error_fielder = (
            None  # int 1-9 if error on fielder (PO only)
        )
        self.detail_pickoff_awaiting_error_fielder = False
        # Initialize runner-advancement builder state
        self.runner_tokens = []  # collected tokens like '1-2', '2X3(25)', 'SB2'
        self.advance_from_base = None  # for BK/DI/PB/WP path
        # OA-specific staged builder
        self.oa_stage = "choose_runner"
        self.oa_from_base = None
        self.oa_out = False
        self.oa_dest = None
        self.oa_fielders = []
        # SB builder (toggle set of bases)
        self.sb_targets = set()
        # Ensure flags exist for PB/WP pitch-triggered flow
        if not hasattr(self, "detail_mode_from_pitch_pb_wp"):
            self.detail_mode_from_pitch_pb_wp = False
            self.detail_mode_pb_wp_code = None

    def _handle_detail_mode_input(self, key: str) -> None:
        """Handle input in detail mode."""
        # Handle different types of plays
        if self.detail_mode_result in ["OUT", "GDP", "LDP", "TP", "FO", "UO"]:
            # Out types need out type and fielding positions (K allows optional fielders)
            if self.detail_mode_out_type is None and key in self.out_type_hotkeys:
                self.detail_mode_out_type = self.out_type_hotkeys[key]
            elif (
                self.detail_mode_out_type is not None
                and key in self.fielding_position_hotkeys
            ):
                # Add fielding position to the list (always allowed; optional for K)
                self.detail_mode_fielders.append(self.fielding_position_hotkeys[key])

                # Don't automatically save - let user press ENTER when done selecting fielders
                # This allows for multi-fielder plays like 6-4-3 double plays
        elif self.detail_mode_result in ["PO", "POCS", "CS"]:
            # Pickoffs require base selection and either a fielder sequence (for outs) or error (PO only)
            if self.detail_pickoff_base is None:
                # Select base: PO -> 1/2/3, POCS -> 2/3/4 (4 represents home 'H')
                if key in ["1", "2", "3"] and self.detail_mode_result == "PO":
                    self.detail_pickoff_base = key
                elif key in ["2", "3", "4"] and self.detail_mode_result in [
                    "POCS",
                    "CS",
                ]:
                    self.detail_pickoff_base = "H" if key == "4" else key
            else:
                # If awaiting error fielder for PO
                if (
                    self.detail_mode_result == "PO"
                    and self.detail_pickoff_awaiting_error_fielder
                    and key in self.fielding_position_hotkeys
                ):
                    self.detail_pickoff_error_fielder = self.fielding_position_hotkeys[
                        key
                    ]
                    self.detail_pickoff_awaiting_error_fielder = False
                # Start selecting error fielder (PO only). Use 'e' to mark error on next fielder digit
                elif (
                    self.detail_mode_result == "PO"
                    and key == "e"
                    and self.detail_pickoff_error_fielder is None
                ):
                    self.detail_pickoff_awaiting_error_fielder = True
                # Otherwise collect fielder sequence digits
                elif key in self.fielding_position_hotkeys:
                    self.detail_pickoff_fielders.append(
                        self.fielding_position_hotkeys[key]
                    )
        elif self.detail_mode_result in ["BK", "DI", "PB", "WP", "SB", "OA"]:
            # Runner advancement builder
            if self.detail_mode_result == "SB":
                # Toggle stolen base tokens SB2/SB3/SBH using keys 2,3,4/H
                if key in ["2", "3", "4", "h"]:
                    target = "H" if key in ["4", "h"] else key
                    if target in self.sb_targets:
                        self.sb_targets.remove(target)
                    else:
                        self.sb_targets.add(target)
                # ENTER handled in main loop to save
            elif self.detail_mode_result in ["BK", "DI", "PB", "WP"]:
                # Simple advance: choose from base then destination
                # If a strikeout was already recorded for this play, allow batter (B) -> 1
                current_game = self.event_file.games[self.current_game_index]
                current_play = current_game.plays[self.current_play_index]
                is_strikeout_recorded = bool(
                    (current_play.play_description or "").startswith("K")
                )
                if self.advance_from_base is None:
                    if key in ["1", "2", "3"]:
                        self.advance_from_base = key
                    elif is_strikeout_recorded and key in ["b", "B"]:
                        self.advance_from_base = "B"
                elif self.advance_from_base is not None:
                    from_b = self.advance_from_base
                    if from_b == "1" and key == "2":
                        self.runner_tokens.append("1-2")
                        self.advance_from_base = None
                    elif from_b == "2" and key == "3":
                        self.runner_tokens.append("2-3")
                        self.advance_from_base = None
                    elif from_b == "3" and key in ["4", "h"]:
                        self.runner_tokens.append("3-H")
                        self.advance_from_base = None
                    elif from_b == "B" and key in ["1", "2", "3", "4", "h"]:
                        dest = {
                            "1": "1",
                            "2": "2",
                            "3": "3",
                            "4": "H",
                            "h": "H",
                        }[key]
                        self.runner_tokens.append(f"B-{dest}")
                        self.advance_from_base = None
            else:  # OA builder
                if self.oa_stage == "choose_runner" and key in ["1", "2", "3"]:
                    self.oa_from_base = key
                    self.oa_stage = "choose_action"
                elif self.oa_stage == "choose_action" and key in ["-", "x"]:
                    self.oa_out = key == "x"
                    self.oa_stage = "choose_dest"
                elif self.oa_stage == "choose_dest":
                    if self.oa_from_base == "1" and key == "2":
                        self.oa_dest = "2"
                    elif self.oa_from_base == "2" and key == "3":
                        self.oa_dest = "3"
                    elif self.oa_from_base == "3" and key in ["4", "h"]:
                        self.oa_dest = "H"
                    if self.oa_dest:
                        if self.oa_out:
                            self.oa_stage = "choose_fielders"
                            self.oa_fielders = []
                        else:
                            # finalize simple advance token
                            self.runner_tokens.append(
                                f"{self.oa_from_base}-{self.oa_dest}"
                            )
                            # reset OA builder
                            self.oa_stage = "choose_runner"
                            self.oa_from_base = None
                            self.oa_out = False
                            self.oa_dest = None
                    # else: wait for valid dest
                elif self.oa_stage == "choose_fielders":
                    if key in self.fielding_position_hotkeys:
                        self.oa_fielders.append(self.fielding_position_hotkeys[key])
                    elif key in ["\r", "\n"]:
                        # require at least one fielder
                        if not self.oa_fielders:
                            return
                        seq = "".join(map(str, self.oa_fielders))
                        self.runner_tokens.append(
                            f"{self.oa_from_base}X{self.oa_dest}({seq})"
                        )
                        # reset OA builder
                        self.oa_stage = "choose_runner"
                        self.oa_from_base = None
                        self.oa_out = False
                        self.oa_dest = None
                        self.oa_fielders = []
        else:
            # Regular hits need hit type and fielding position
            if key in self.hit_type_hotkeys:
                self.detail_mode_hit_type = self.hit_type_hotkeys[key]
            elif (
                self.detail_mode_hit_type is not None
                and key in self.fielding_position_hotkeys
            ):
                # For hits, we only need one fielding position
                self.detail_mode_fielders.append(self.fielding_position_hotkeys[key])

                # Automatically save and progress to next batter when both selections are complete
                if (
                    self.detail_mode_result
                    and self.detail_mode_hit_type
                    and self.detail_mode_fielders
                ):
                    self._save_detail_mode_result()

    def _save_detail_mode_result(self) -> None:
        """Save the detailed play result and exit detail mode."""
        # Handle pickoffs and caught stealing (PO, POCS, CS)
        if self.detail_mode_result in ["PO", "POCS", "CS"]:
            # Validate selections
            if not self.detail_pickoff_base:
                self.console.print(
                    "Please select the base (1/2/3 for PO; 2/3/H for POCS/CS)",
                    style="yellow",
                )
                return
            if self.detail_mode_result == "PO":
                # Either error on a fielder OR at least one fielder in sequence to record an out
                if (
                    self.detail_pickoff_error_fielder is None
                    and not self.detail_pickoff_fielders
                ):
                    self.console.print(
                        "Select fielder sequence (e.g., 13) or mark error with 'E' then fielder.",
                        style="yellow",
                    )
                    return
                if self.detail_pickoff_error_fielder is not None:
                    desc = f"PO{self.detail_pickoff_base}(E{self.detail_pickoff_error_fielder})"
                else:
                    seq = "".join(str(f) for f in self.detail_pickoff_fielders)
                    desc = f"PO{self.detail_pickoff_base}({seq})"
            elif self.detail_mode_result == "POCS":
                if not self.detail_pickoff_fielders:
                    self.console.print(
                        "Select fielder sequence for POCS (e.g., 1361)", style="yellow"
                    )
                    return
                seq = "".join(str(f) for f in self.detail_pickoff_fielders)
                base_token = self.detail_pickoff_base
                desc = f"POCS{base_token}({seq})"
            else:  # CS
                if not self.detail_pickoff_fielders:
                    self.console.print(
                        "Select fielder sequence for CS (e.g., 26)", style="yellow"
                    )
                    return
                seq = "".join(str(f) for f in self.detail_pickoff_fielders)
                base_token = self.detail_pickoff_base
                desc = f"CS{base_token}({seq})"

            # Apply to current play
            current_game = self.event_file.games[self.current_game_index]
            current_play = current_game.plays[self.current_play_index]
            self._save_state_for_undo()
            current_play.play_description = desc
            current_play.edited = True
            self._save_current_state()

            # Exit detail mode after pickoff save
            self._reset_detail_mode()
            self.mode = "pitch"
            return

        # Handle runner advancement events (BK, DI, PB, WP, SB, OA)
        if self.detail_mode_result in ["BK", "DI", "PB", "WP", "SB", "OA"]:
            # Build description string
            current_game = self.event_file.games[self.current_game_index]
            current_play = current_game.plays[self.current_play_index]
            self._save_state_for_undo()
            if self.detail_mode_result == "SB":
                # From toggled set
                if not self.sb_targets:
                    self.console.print(
                        "Select at least one stolen base", style="yellow"
                    )
                    return
                # produce stable order 2,3,H
                parts = []
                for b in ["2", "3", "H"]:
                    if b in self.sb_targets:
                        parts.append(f"SB{b}")
                desc = ";".join(parts)
                current_play.play_description = desc
            else:
                # For BK/DI/PB/WP/OA use CODE.<tokens>
                if not self.runner_tokens:
                    self.console.print(
                        "Add at least one runner advance (e.g., 1-2)", style="yellow"
                    )
                    return
                # If PB/WP was initiated from pitch entry, append as a suffix
                # to the existing play result: "+PB.2-3" or "+WP.1-2;3-H".
                if self.detail_mode_result in ["PB", "WP"] and getattr(
                    self, "detail_mode_from_pitch_pb_wp", False
                ):
                    suffix = (
                        "+"
                        + self.detail_mode_result
                        + "."
                        + ";".join(self.runner_tokens)
                    )
                    base_desc = current_play.play_description or ""
                    current_play.play_description = base_desc + suffix
                else:
                    desc = f"{self.detail_mode_result}." + ";".join(self.runner_tokens)
                    current_play.play_description = desc
            current_play.edited = True
            self._save_current_state()

            # Exit detail mode
            self._reset_detail_mode()
            self.mode = "pitch"
            # Reset PB/WP pitch-trigger flag after saving advances
            if hasattr(self, "detail_mode_from_pitch_pb_wp"):
                self.detail_mode_from_pitch_pb_wp = False
                self.detail_mode_pb_wp_code = None
            return

        # Check if we have the required selections based on play type
        if self.detail_mode_result in ["OUT", "GDP", "LDP", "TP", "FO", "UO"]:
            # Out types need out type and fielding positions
            if (
                self.detail_mode_result
                and self.detail_mode_out_type
                and self.detail_mode_fielders
            ):
                # Generate the detailed play description
                play_description = self._generate_detailed_play_description(
                    self.detail_mode_result,
                    self.detail_mode_out_type,
                    self.detail_mode_fielders,
                )

                # Set the play result
                current_game = self.event_file.games[self.current_game_index]
                current_play = current_game.plays[self.current_play_index]

                # Save state before making changes
                self._save_state_for_undo()

                # Preserve any previously appended runner-advancement suffix (e.g., +PB.2-3)
                existing = current_play.play_description or ""
                suffix_idx = existing.find("+")
                suffix = existing[suffix_idx:] if suffix_idx != -1 else ""
                current_play.play_description = play_description + suffix
                # Append 'X' to pitches for balls put in play on outs, except strikeouts
                if self.detail_mode_out_type != "K":
                    self._ensure_ball_in_play_marker()
                current_play.edited = True
                self._save_current_state()

                # After saving an out with fielders, automatically enter the
                # Hit Location builder so the user can add location immediately.
                # Remain in detail mode.
                self._start_modifier_detail_mode()
                # Auto-open Hit Location builder
                self.selected_modifier_group = "h"
                self.hit_location_active = True
                self.hit_location_positions = ""
                self.hit_location_suffix = ""
                self.hit_location_depth = ""
                self.hit_location_foul = False
            else:
                self.console.print(
                    "Please complete all detail selections", style="yellow"
                )
        elif self.detail_mode_result in ["SF", "SH"]:
            # Sacrifice plays need hit type and fielding positions
            if (
                self.detail_mode_result
                and self.detail_mode_hit_type
                and self.detail_mode_fielders
            ):
                # Generate the detailed play description
                play_description = self._generate_detailed_play_description(
                    self.detail_mode_result,
                    self.detail_mode_hit_type,
                    self.detail_mode_fielders[0] if self.detail_mode_fielders else 0,
                )

                # Set the play result
                current_game = self.event_file.games[self.current_game_index]
                current_play = current_game.plays[self.current_play_index]

                # Save state before making changes
                self._save_state_for_undo()

                # Preserve any previously appended runner-advancement suffix (e.g., +PB.2-3)
                existing = current_play.play_description or ""
                suffix_idx = existing.find("+")
                suffix = existing[suffix_idx:] if suffix_idx != -1 else ""
                current_play.play_description = play_description + suffix
                # Append 'X' to pitches for balls put in play on sacrifice plays
                self._ensure_ball_in_play_marker()
                current_play.edited = True
                self._save_current_state()

                # After saving a sacrifice play, automatically enter the
                # runner advance detail mode wizard
                self._start_modifier_detail_mode()
                # Auto-open Advance Runner wizard
                self.selected_modifier_group = "r"
                self.advance_runner_active = True
                self.advance_runner_from_base = None
            else:
                self.console.print(
                    "Please complete all detail selections", style="yellow"
                )
        else:
            # Regular hits: allow saving with or without a fielding position
            if self.detail_mode_result and self.detail_mode_hit_type:
                # Generate the detailed play description
                play_description = self._generate_detailed_play_description(
                    self.detail_mode_result,
                    self.detail_mode_hit_type,
                    (
                        self.detail_mode_fielders[0] if self.detail_mode_fielders else 0
                    ),  # 0 indicates no position
                )

                # Set the play result
                current_game = self.event_file.games[self.current_game_index]
                current_play = current_game.plays[self.current_play_index]

                # Save state before making changes
                self._save_state_for_undo()

                # Preserve any previously appended runner-advancement suffix (e.g., +PB.2-3)
                existing = current_play.play_description or ""
                suffix_idx = existing.find("+")
                suffix = existing[suffix_idx:] if suffix_idx != -1 else ""
                current_play.play_description = play_description + suffix
                # Append 'X' to pitches for balls put in play on hits
                self._ensure_ball_in_play_marker()
                current_play.edited = True
                self._save_current_state()

                # After saving a hit/error, automatically enter the
                # Hit Location builder so the user can add location immediately.
                # Remain in detail mode; do not auto-advance until modifiers finish.
                self._start_modifier_detail_mode()
                # Auto-open Hit Location builder
                self.selected_modifier_group = "h"
                self.hit_location_active = True
                self.hit_location_positions = ""
                self.hit_location_suffix = ""
                self.hit_location_depth = ""
                self.hit_location_foul = False
            else:
                self.console.print(
                    "Please complete all detail selections", style="yellow"
                )

    def _generate_detailed_play_description(
        self, result: str, hit_type: str, fielders
    ) -> str:
        """Generate detailed Retrosheet play description with hit type and fielding positions."""
        # Handle fielders parameter - can be int (single) or list (multiple)
        if isinstance(fielders, int):
            fielding_position = fielders
            fielders_list = [fielders]
        else:
            fielding_position = fielders[0] if fielders else 0
            fielders_list = fielders

        if result == "S":  # Single
            return (
                f"S/{hit_type}"
                if fielding_position <= 0
                else f"S{fielding_position}/{hit_type}"
            )
        elif result == "D":  # Double
            return (
                f"D/{hit_type}"
                if fielding_position <= 0
                else f"D{fielding_position}/{hit_type}"
            )
        elif result == "T":  # Triple
            return (
                f"T/{hit_type}"
                if fielding_position <= 0
                else f"T{fielding_position}/{hit_type}"
            )
        elif result == "HR":  # Home run
            return f"HR/{hit_type}" if fielding_position <= 0 else f"HR/{hit_type}"
        elif result == "E":  # Error
            return (
                f"E/{hit_type}"
                if fielding_position <= 0
                else f"E{fielding_position}/{hit_type}"
            )
        elif result == "FC":  # Fielder's choice
            return (
                f"FC/{hit_type}"
                if fielding_position <= 0
                else f"FC{fielding_position}/{hit_type}"
            )
        elif result == "SF":  # Sacrifice fly
            return (
                f"SF/{hit_type}"
                if fielding_position <= 0
                else f"SF{fielding_position}/{hit_type}"
            )
        elif result == "SH":  # Sacrifice bunt
            return (
                f"SH/{hit_type}"
                if fielding_position <= 0
                else f"SH{fielding_position}/{hit_type}"
            )
        elif result in ["OUT", "GDP", "LDP", "TP", "FO", "UO"]:
            # New formatting for outs: fielders first, then out type(s)
            out_type = hit_type  # may be base (G/L/F/P/B/SF/SH/K/FC/DP) or special (FO/UO/GDP/LDP/TP)
            fielder_string = "".join(str(f) for f in fielders_list)
            # Strikeout special case: K with optional immediate fielder sequence (e.g., K23)
            if out_type == "K":
                return "K" + (fielder_string if fielder_string else "")

            tokens = [fielder_string] if fielder_string else [str(fielding_position)]

            # Always include the selected out_type if provided
            if out_type:
                tokens.append(out_type)

            # Append the specific result modifier if applicable and not duplicated
            if result in ["FO", "UO", "GDP", "LDP", "TP"] and result != out_type:
                tokens.append(result)

            return "/".join(tokens)
        else:
            # For other results, use the basic format
            return self._generate_retrosheet_play_description(result, fielding_position)

    def _reset_detail_mode(self) -> None:
        """Reset detail mode state."""
        self.detail_mode_result = None
        self.detail_mode_hit_type = None
        self.detail_mode_out_type = None
        self.detail_mode_fielders = []
        self.detail_mode_runner_outs = []
        self.modifier_selection_active = False
        self.selected_modifier_group = None
        self.selected_modifiers = []
        self.modifier_param_request = None
        self.current_modifier_options_keymap = {}
        self.modifiers_live_applied = False
        # Reset pickoff state
        self.detail_pickoff_base = None
        self.detail_pickoff_fielders = []
        self.detail_pickoff_error_fielder = None
        self.detail_pickoff_awaiting_error_fielder = False
        # Reset runner-advancement state
        self.runner_tokens = []
        self.advance_from_base = None
        self.oa_stage = "choose_runner"
        self.oa_from_base = None
        self.oa_out = False
        self.oa_dest = None
        self.oa_fielders = []
        self.sb_targets = set()
        # Reset advance-runner (modifiers UI) state
        self.advance_runner_active = False
        self.advance_runner_from_base = None
        self.advance_runner_tokens = []

    def _start_modifier_detail_mode(self) -> None:
        """Begin the additional details selection UI inside detail mode."""
        self.modifier_selection_active = True
        self.selected_modifier_group = None
        self.selected_modifiers = []
        self.modifier_param_request = None
        self.current_modifier_options_keymap = {}
        self.modifiers_live_applied = True  # enable live append behavior

    def _handle_modifier_mode_input(self, key: str) -> None:
        """Handle input when selecting additional (auxiliary) play details."""
        # If we're in the Hit Location wizard, handle keys here first
        if self.selected_modifier_group == "h":
            if self._handle_hit_location_input(key):
                return

        # Finish and apply modifiers (only when not inside a wizard)
        if key in ["\r", "\n"] and not (
            self.selected_modifier_group == "r"
            and getattr(self, "advance_runner_active", False)
        ):
            self._apply_modifiers_to_current_play()
            # Return to pitch mode after applying modifiers
            self.mode = "pitch"
            self._reset_detail_mode()
            return

        # Back to group selection
        if key == "0":
            self.selected_modifier_group = None
            self.modifier_param_request = None
            self.current_modifier_options_keymap = {}
            return

        # If awaiting a parameter for a modifier
        if self.modifier_param_request:
            code = self.modifier_param_request["code"]
            if (
                self.modifier_param_request["type"] == "fielder"
                and key in self.fielding_position_hotkeys
            ):
                suffix = str(self.fielding_position_hotkeys[key])
                resolved = code.replace("$", suffix)
                self._append_modifier_to_current_play(resolved)
                self.modifier_param_request = None
            elif self.modifier_param_request["type"] == "base" and key in [
                "1",
                "2",
                "3",
                "4",
            ]:
                resolved = code.replace("%", key)
                self._append_modifier_to_current_play(resolved)
                self.modifier_param_request = None
            return

        # Choose group
        if self.selected_modifier_group is None:
            if key in self.modifier_groups:
                self.selected_modifier_group = key
                # Initialize Hit Location builder state if chosen
                if key == "h":
                    self.hit_location_active = True
                    self.hit_location_positions = ""
                    self.hit_location_suffix = ""
                    self.hit_location_depth = ""
                elif key == "r":
                    # Start Advance Runner builder inside modifiers UI
                    self.advance_runner_active = True
                    self.advance_runner_from_base = None
                return
            return

        # Choose option within group
        if key in self.current_modifier_options_keymap:
            code = self.current_modifier_options_keymap[key]
            # Codes that require parameter
            if code == "E$":
                self.modifier_param_request = {"code": "E$", "type": "fielder"}
            elif code == "R$":
                self.modifier_param_request = {"code": "R$", "type": "fielder"}
            elif code == "TH%":
                self.modifier_param_request = {"code": "TH%", "type": "base"}
            else:
                self._append_modifier_to_current_play(code)
        # Any other key ignored

        # Handle Advance Runner wizard keys
        if self.selected_modifier_group == "r" and self.advance_runner_active:
            # Back to groups
            if key == "0":
                self.selected_modifier_group = None
                self.advance_runner_active = False
                self.advance_runner_from_base = None
                return
            # Save/apply tokens to play and remain in modifiers UI
            if key in ["\r", "\n"]:
                if self.advance_runner_tokens:
                    current_game = self.event_file.games[self.current_game_index]
                    current_play = current_game.plays[self.current_play_index]
                    if current_play.play_description:
                        if "." in current_play.play_description:
                            current_play.play_description += ";" + ";".join(
                                self.advance_runner_tokens
                            )
                        else:
                            current_play.play_description += "." + ";".join(
                                self.advance_runner_tokens
                            )
                        current_play.edited = True
                        self._save_current_state()
                self.advance_runner_active = False
                self.advance_runner_from_base = None
                self.advance_runner_tokens = []
                self.selected_modifier_group = None
                return
            # Choose from-base
            if self.advance_runner_from_base is None and key in ["1", "2", "3"]:
                self.advance_runner_from_base = key
                return
            # Choose dest based on from-base; allow explicitly no-advance token like 3-3
            if self.advance_runner_from_base is not None:
                fb = self.advance_runner_from_base
                dest = None
                if fb == "1" and key in ["1", "2"]:
                    dest = "2" if key == "2" else "1"
                elif fb == "2" and key in ["2", "3"]:
                    dest = "3" if key == "3" else "2"
                elif fb == "3" and key in ["3", "4", "h"]:
                    dest = "H" if key in ["4", "h"] else "3"
                if dest:
                    token = f"{fb}-{dest}"
                    self.advance_runner_tokens.append(token)
                    self.advance_runner_from_base = None
                return

    def _render_hit_location_builder(self, controls_text: Text) -> None:
        """Render the Hit Location builder UI inside the modifiers panel."""
        # Positions
        pos_display = self.hit_location_positions or "(none)"
        controls_text.append("Positions (enter 1-2 digits [1-9]): ", style="bold blue")
        controls_text.append(f"{pos_display}\n")

        # M / L toggles based on positions
        allow_m = any(ch in ["4", "6"] for ch in self.hit_location_positions)
        # L only applies for exactly 7 or 9, not multi-position like 78 or 89
        allow_l = self.hit_location_positions in ["7", "9"]

        if allow_m:
            m_state = "ON" if self.hit_location_suffix == "M" else "OFF"
            controls_text.append("[M] Midfield (4/6 only): ", style="bold blue")
            controls_text.append(f"{m_state}\n", style="bold cyan")
        if allow_l:
            l_state = "ON" if self.hit_location_suffix == "L" else "OFF"
            controls_text.append(
                "[L] Near the foul line (7/9 only): ", style="bold blue"
            )
            controls_text.append(f"{l_state}\n", style="bold cyan")

        # Foul territory toggle (for exact positions 2,3,5,7,9 or dual 23/25)
        allow_f = self.hit_location_positions in ["2", "3", "5", "7", "9", "23", "25"]
        if allow_f:
            f_state = "ON" if self.hit_location_foul else "OFF"
            controls_text.append(
                "[F] Foul territory (2/3/5/7/9 or 23/25): ", style="bold blue"
            )
            controls_text.append(f"{f_state}\n", style="bold cyan")

        # Depth selection
        depth_display = self.hit_location_depth or "Normal"
        controls_text.append(
            "Depth: [S] Shallow  [N] Normal  [D] Deep  [X] Extra Deep (XD)\n",
            style="bold blue",
        )
        controls_text.append(f"Current: {depth_display}\n", style="bold cyan")

        # Instructions
        controls_text.append("[0] Back  [ENTER] Add to play\n", style="bold blue")

    def _handle_hit_location_input(self, key: str) -> bool:
        """Handle input for the Hit Location builder. Returns True if handled."""
        if not self.hit_location_active:
            return False

        # Back to group selection
        if key == "0":
            self.selected_modifier_group = None
            self.hit_location_active = False
            self.hit_location_positions = ""
            self.hit_location_suffix = ""
            self.hit_location_depth = ""
            self.hit_location_foul = False
            return True

        # Enter digits for positions (up to 2)
        if key in [str(d) for d in range(1, 10)]:
            if len(self.hit_location_positions) < 2:
                self.hit_location_positions += key
            return True

        # Toggle M (only when positions include 4 or 6)
        if key == "m":
            if any(ch in ["4", "6"] for ch in self.hit_location_positions):
                self.hit_location_suffix = (
                    "M" if self.hit_location_suffix != "M" else ""
                )
            return True

        # Toggle L (only when positions include 7 or 9)
        if key == "l":
            if self.hit_location_positions in ["7", "9"]:
                self.hit_location_suffix = (
                    "L" if self.hit_location_suffix != "L" else ""
                )
            return True

        # Toggle F (only when positions are exactly 2,3,5,7,9, or dual 23/25)
        if key == "f":
            if self.hit_location_positions in ["2", "3", "5", "7", "9", "23", "25"]:
                self.hit_location_foul = not self.hit_location_foul
            return True

        # Depth selection
        if key == "s":
            self.hit_location_depth = "S"
            return True
        if key == "n":
            self.hit_location_depth = ""  # Normal depth has no code
            return True
        if key == "d":
            self.hit_location_depth = "D"
            return True
        if key == "x":
            self.hit_location_depth = "XD"
            return True

        # Apply on ENTER if valid
        if key in ["\r", "\n"]:
            # Require at least one position digit
            if not self.hit_location_positions:
                return True  # ignore until valid
            # Build code: positions + optional suffix + depth
            code = self.hit_location_positions
            if self.hit_location_suffix:
                code += self.hit_location_suffix
            if self.hit_location_depth:
                code += self.hit_location_depth
            if self.hit_location_foul:
                code += "F"
            self._append_hit_location_to_current_play(code)
            # Reset builder and return to group selection (stay in modifiers UI)
            self.hit_location_active = False
            self.selected_modifier_group = None
            self.hit_location_positions = ""
            self.hit_location_suffix = ""
            self.hit_location_depth = ""
            self.hit_location_foul = False
            return True

        return False

    def _append_hit_location_to_current_play(self, code: str) -> None:
        """Append hit location code without a slash separator to the current play."""
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]
        if not current_play.play_description:
            return
        # If this is the first hit-location append after the hit type token (e.g., after '/G'),
        # prefix the primary fielder once. Subsequent appends should not re-prefix.
        fielder = self._extract_primary_fielder_from_play_description(
            current_play.play_description
        )
        tail_after_slash = current_play.play_description.split("/")[-1]
        is_first_append = tail_after_slash in {"G", "L", "F", "P", "B"}
        # Prefix the primary fielder only for infielders (1-6); for outfielders (7-9), don't prefix
        should_prefix = (
            bool(fielder) and is_first_append and int(fielder) in {1, 2, 3, 4, 5, 6}
        )
        prefixed_code = f"{fielder}{code}" if should_prefix else code
        # Append directly without space or slash
        current_play.play_description += f"{prefixed_code}"
        current_play.edited = True
        self._save_current_state()

    def _extract_primary_fielder_from_play_description(self, desc: str):
        """Extract the primary fielder digit immediately following the result token before '/'.

        Examples:
        - S6/G -> 6
        - D7/L -> 7
        - E6/G -> 6
        - FC6/G -> 6
        - HR/F -> None (no fielder)
        """
        # Match leading letters, then capture digits before the first '/'
        match = re.match(r"^[A-Z]+(\d+)/", desc)
        if match:
            digits = match.group(1)
            # Only return the first digit (positions are 1..9)
            try:
                return int(digits[0])
            except (ValueError, IndexError):
                return None
        return None

    def _apply_modifiers_to_current_play(self) -> None:
        """Append selected modifiers to the current play description and save."""
        if self.modifiers_live_applied or not self.selected_modifiers:
            return
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]
        current_play.play_description = (
            current_play.play_description or ""
        ) + self._format_modifiers_suffix()
        current_play.edited = True
        self._save_current_state()

    def _append_modifier_to_current_play(self, code: str) -> None:
        """Append a single modifier code immediately to the current play and record it for UI."""
        self.selected_modifiers.append(code)
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]
        # Ensure there is a primary result
        if not current_play.play_description:
            return
        # Avoid duplicate slashes
        if not current_play.play_description.endswith("/"):
            current_play.play_description += f"/{code}"
        else:
            current_play.play_description += code
        current_play.edited = True
        self._save_current_state()

    def _format_modifiers_suffix(self) -> str:
        """Format the suffix string for selected modifiers in Retrosheet style."""
        # Retrosheet modifiers typically follow with "/" joining tokens
        # Ensure codes are space-free and already replacement-handled
        return "/" + "/".join(self.selected_modifiers)

    def _add_modifier_options_wrapped(self, controls_text: Text, codes: list) -> None:
        """Render modifier options on wrapped rows within a max width, building keymap a..z."""
        # Reset keymap for current group view
        self.current_modifier_options_keymap = {}

        max_width = min(self.console.width, 120)
        available_width = max_width - 2  # account for indentation

        current_row = []
        current_row_width = 0

        letter_ord = ord("a")
        for code in codes:
            key_char = chr(letter_ord)
            self.current_modifier_options_keymap[key_char] = code
            desc = self.modifier_descriptions.get(code, code)
            entry = f"[{key_char.upper()}] {code} - {desc}"

            entry_width = len(entry)
            spacing_width = 2 if current_row else 0
            total_entry_width = entry_width + spacing_width

            if current_row_width + total_entry_width <= available_width:
                current_row.append(entry)
                current_row_width += total_entry_width
            else:
                if current_row:
                    controls_text.append("  " + "  ".join(current_row) + "\n")
                current_row = [entry]
                current_row_width = entry_width

            letter_ord += 1

        if current_row:
            controls_text.append("  " + "  ".join(current_row) + "\n")

    def _add_modifier_group_controls_wrapped(self, controls_text: Text) -> None:
        """Render the modifier group list wrapped across lines within a max width."""
        max_width = min(self.console.width, 120)
        available_width = max_width - 2

        # Build entries like "[B] Ball Types"
        entries = []
        for key, (name, _) in self.modifier_groups.items():
            entries.append(f"[{str(key).upper()}] {name}")

        current_row = []
        current_row_width = 0

        for entry in entries:
            entry_width = len(entry)
            spacing_width = 2 if current_row else 0
            total_entry_width = entry_width + spacing_width

            if current_row_width + total_entry_width <= available_width:
                current_row.append(entry)
                current_row_width += total_entry_width
            else:
                if current_row:
                    controls_text.append("  " + "  ".join(current_row) + "\n")
                current_row = [entry]
                current_row_width = entry_width

        if current_row:
            controls_text.append("  " + "  ".join(current_row) + "\n")


def run_editor(event_file_path: Path, output_dir: Path) -> None:
    """Run the interactive editor."""
    try:
        # Validate shortcuts before starting the editor
        validate_shortcuts()

        event_file = parse_event_file(event_file_path)
        editor = RetrosheetEditor(event_file, output_dir)
        editor.run()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
