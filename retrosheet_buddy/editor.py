"""Interactive editor for Retrosheet event files."""

import platform
import sys
from pathlib import Path
from typing import List, Tuple

import click
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import EventFile, Game
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
                    # Define navigation shortcuts (work in all modes)
    navigation_shortcuts = {
        'q': 'Quit',
        'left': 'Previous play',
        'right': 'Next play',
        'tab': 'Switch modes',
        'x': 'Undo last action',
        '-': 'Clear (pitches in PITCH mode, result in PLAY mode)',
        '\r': 'Enter key',
        '\n': 'Enter key',
    }
    
    # Define mode shortcuts from the editor
    pitch_shortcuts = {
        'b': 'Ball',
        's': 'Swinging strike',
        'f': 'Foul',
        'c': 'Called strike',
        't': 'Foul tip',
        'm': 'Missed bunt',
        'p': 'Pitchout',
        'i': 'Intentional ball',
        'h': 'Hit batter',
        'v': 'Wild pitch',
        'a': 'Passed ball',
        '*': 'Swinging on pitchout',
        'r': 'Foul on pitchout',
        'e': 'Foul bunt',
        'n': 'No pitch',
        'o': 'Foul on bunt',
        'u': 'Unknown',
    }
    
    play_shortcuts = {
        'w': 'Out',
        '1': 'Single',
        '2': 'Double',
        '3': 'Triple',
        '4': 'Home run',
        'k': 'Strikeout',
        'l': 'Walk',
        'y': 'Hit by pitch',
        'z': 'Error',
        'g': "Fielder's choice",
        'j': 'Double play',
        '5': 'Triple play',
        '6': 'Sacrifice fly',
        '7': 'Sacrifice bunt',
        '8': 'Intentional walk',
        '9': 'Catcher interference',
        '0': 'Out advancing',
        ';': 'No play',
        '#': 'Grounded into double play',
        'd': 'Lined into double play',
        '[': 'Force out',
        ']': 'Unassisted out',
    }
    
    # Detail mode shortcuts (only active in detail mode)
    hit_type_shortcuts = {
        'g': 'Grounder',
        'l': 'Line drive',
        'f': 'Fly ball',
        'p': 'Pop up',
        'b': 'Bunt',
    }
    
    fielding_position_shortcuts = {
        '1': 'Pitcher',
        '2': 'Catcher',
        '3': 'First base',
        '4': 'Second base',
        '5': 'Third base',
        '6': 'Shortstop',
        '7': 'Left field',
        '8': 'Center field',
        '9': 'Right field',
    }
    
    out_type_shortcuts = {
        'g': 'Ground out',
        'l': 'Line out',
        'f': 'Fly out',
        'p': 'Pop out',
        'b': 'Bunt out',
        's': 'Sacrifice fly',
        'h': 'Sacrifice hit/bunt',
        'w': 'Grounded into double play',
        '!': 'Lined into double play',
        'y': 'Triple play',
        'z': 'Force out',
        '[': 'Unassisted out',
    }
    
    # Check for conflicts between navigation and mode shortcuts
    conflicts: List[Tuple[str, str, str, str]] = []
    
    # Check navigation vs pitch mode conflicts
    for key in navigation_shortcuts:
        if key in pitch_shortcuts:
            conflicts.append((
                key,
                navigation_shortcuts[key],
                'navigation',
                f"pitch mode: {pitch_shortcuts[key]}"
            ))
    
    # Check navigation vs play mode conflicts
    for key in navigation_shortcuts:
        if key in play_shortcuts:
            conflicts.append((
                key,
                navigation_shortcuts[key],
                'navigation',
                f"play mode: {play_shortcuts[key]}"
            ))
    
    # Check navigation vs detail mode conflicts
    detail_mode_shortcuts = {
        **hit_type_shortcuts,
        **fielding_position_shortcuts,
        **out_type_shortcuts,
    }
    
    for key in navigation_shortcuts:
        if key in detail_mode_shortcuts:
            conflicts.append((
                key,
                navigation_shortcuts[key],
                'navigation',
                f"detail mode: {detail_mode_shortcuts[key]}"
            ))
    
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
        
        error_message += "Navigation shortcuts must have exclusive access to their keys.\n"
        error_message += "Please reassign conflicting mode shortcuts to different keys.\n"
        error_message += "All conflicts must be resolved for proper editor functionality."
        
        raise ValueError(error_message)


def get_key() -> str:
    """Get a single key press without requiring Enter."""
    if platform.system() == "Windows":
        import msvcrt
        key = msvcrt.getch()
        if key == b'\xe0':  # Extended key
            key = msvcrt.getch()
            if key == b'H':
                return 'up'
            elif key == b'P':
                return 'down'
            elif key == b'K':
                return 'left'
            elif key == b'M':
                return 'right'
        decoded_key = key.decode('utf-8', errors='ignore')
        # Handle TAB key
        if decoded_key == '\t':
            return 'tab'
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
                if ch == '\x1b':  # Escape sequence
                    next_ch = sys.stdin.read(1)
                    if next_ch == '[':
                        third_ch = sys.stdin.read(1)
                        if third_ch == 'A':
                            return 'up'
                        elif third_ch == 'B':
                            return 'down'
                        elif third_ch == 'C':
                            return 'right'
                        elif third_ch == 'D':
                            return 'left'
                
                # Handle TAB key
                if ch == '\t':
                    return 'tab'
                
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
        self.mode = 'pitch'  # 'pitch', 'play', or 'detail'
        
        # Detail mode state
        self.detail_mode_result = None  # The play result selected before entering detail mode
        self.detail_mode_hit_type = None  # G, L, F, etc.
        self.detail_mode_fielders = []  # List of fielders for multi-fielder plays (1-9)
        self.detail_mode_out_type = None  # OUT, GDP, LDP, TP, etc.
        self.detail_mode_runner_outs = []  # List of runner outs for force plays, DPs, etc.

        # Additional (auxiliary) detail selection state
        self.modifier_selection_active = False  # When True, detail mode shows additional detail groups/options
        self.selected_modifier_group = None  # Currently selected group key
        self.selected_modifiers = []  # Collected modifier codes to append (e.g., ["AP", "MREV"]) 
        self.modifier_param_request = None  # e.g., { 'code': 'E$', 'type': 'fielder' } or { 'code': 'TH%', 'type': 'base' }
        self.current_modifier_options_keymap = {}  # map single-letter key -> modifier code for current group view
        self.modifiers_live_applied = False  # If True, modifiers are applied immediately upon selection
        # Define modifier groups and descriptions
        self.modifier_descriptions = {
            # Bunt-related
            'BP': 'Bunt pop up',
            'BG': 'Ground ball bunt',
            'BGDP': 'Bunt grounded into double play',
            'BL': 'Line drive bunt',
            'BPDP': 'Bunt popped into double play',
            'SH': 'Sacrifice hit (bunt)',
            # Ball type / plays
            'G': 'Ground ball',
            'L': 'Line drive',
            'F': 'Fly ball',
            'P': 'Pop fly',
            'FL': 'Foul',
            'IF': 'Infield fly rule',
            'DP': 'Unspecified double play',
            'TP': 'Unspecified triple play',
            'GDP': 'Ground ball double play',
            'GTP': 'Ground ball triple play',
            'LDP': 'Lined into double play',
            'LTP': 'Lined into triple play',
            'NDP': 'No double play credited for this play',
            'SF': 'Sacrifice fly',
            'FO': 'Force out',
            # Interference/obstruction
            'BINT': 'Batter interference',
            'INT': 'Interference',
            'RINT': 'Runner interference',
            'UINT': 'Umpire interference',
            'OBS': 'Obstruction (fielder obstructing a runner)',
            'FINT': 'Fan interference',
            # Administrative / courtesy / reviews / misc
            'AP': 'Appeal play',
            'C': 'Called third strike',
            'COUB': 'Courtesy batter',
            'COUF': 'Courtesy fielder',
            'COUR': 'Courtesy runner',
            'MREV': 'Manager challenge of call on the field',
            'UREV': 'Umpire review of call on the field',
            'BOOT': 'Batting out of turn',
            'IPHR': 'Inside the park home run',
            'PASS': 'Runner passed another runner and was called out',
            'BR': 'Runner hit by batted ball',
            'TH': 'Throw',
            'TH%': 'Throw to base %',
            'R$': 'Relay throw from initial fielder to $',
            'E$': 'Error on $',
        }
        self.modifier_groups = {
            # Note: '0' is reserved for "back" in modifier UI; use mnemonic letters for groups
            'b': ('Ball Types', ['G', 'L', 'F', 'P', 'FL', 'IF']),
            's': ('Sacrifices', ['SF', 'SH']),
            'u': ('Bunt Types', ['BP', 'BG', 'BL']),  # 'u' for bUnt to avoid collision with Ball Types
            'd': ('DP/TP (Generic)', ['DP', 'TP']),
            'v': ('DP/TP Variants', ['GDP', 'GTP', 'LDP', 'LTP', 'NDP', 'BGDP', 'BPDP']),
            'i': ('Interference/Obstruction', ['BINT', 'INT', 'RINT', 'FINT', 'UINT', 'OBS']),
            'a': ('Administrative', ['AP', 'BOOT', 'C', 'IPHR', 'PASS', 'BR', 'MREV', 'UREV']),
            'c': ('Courtesy', ['COUB', 'COUF', 'COUR']),
            't': ('Throws/Relays', ['TH', 'TH%', 'R$']),
            'e': ('Errors', ['E$']),
            'h': ('Hit Location', []),
        }

        # Hit Location builder state (used within modifier selection UI)
        self.hit_location_active = False
        self.hit_location_positions = ""  # one or two digits 1-9
        self.hit_location_suffix = ""     # '' or 'M' or 'L'
        self.hit_location_depth = ""      # '' | 'S' | 'D' | 'XD'
        self.hit_location_foul = False     # True to append 'F' at the end
        
        # Undo functionality
        self.undo_history = []  # List of (game_index, play_index, pitches, play_description) tuples
        
        # Hotkey mappings for pitch events (no conflicts)
        self.pitch_hotkeys = {
            'b': 'B',  # Ball
            's': 'S',  # Swinging strike
            'f': 'F',  # Foul
            'c': 'C',  # Called strike
            't': 'T',  # Foul tip
            'm': 'M',  # Missed bunt
            'p': 'P',  # Pitchout
            'i': 'I',  # Intentional ball
            'h': 'H',  # Hit batter
            'v': 'V',  # Wild pitch
            'a': 'A',  # Passed ball
            '*': 'Q',  # Swinging on pitchout
            'r': 'R',  # Foul on pitchout
            'e': 'E',  # Foul bunt
            'n': 'N',  # No pitch
            'o': 'O',  # Foul on bunt
            'u': 'U',  # Unknown
        }
        
        # Hotkey mappings for play results (consolidated to avoid duplication)
        self.play_hotkeys = {
            'w': 'OUT', # Out
            '1': 'S',   # Single
            '2': 'D',   # Double
            '3': 'T',   # Triple
            '4': 'HR',  # Home run
            'k': 'K',   # Strikeout
            'l': 'W',   # Walk
            'y': 'HP',  # Hit by pitch
            'z': 'E',   # Error
            'g': 'FC',  # Fielder's choice
            'j': 'DP',  # Double play
            '5': 'TP',  # Triple play
            '6': 'SF',  # Sacrifice fly
            '7': 'SH',  # Sacrifice bunt
            '8': 'IW',  # Intentional walk
            '9': 'CI',  # Catcher interference
            '0': 'OA',  # Out advancing
            ';': 'ND',  # No play
            '#': 'GDP', # Grounded into double play
            'd': 'LDP', # Lined into double play
            '[': 'FO',  # Force out
            ']': 'UO',  # Unassisted out
        }
        
        # Hotkey mappings for hit types in detail mode
        self.hit_type_hotkeys = {
            'g': 'G',  # Grounder
            'l': 'L',  # Line drive
            'f': 'F',  # Fly ball
            'p': 'P',  # Pop up
            'b': 'B',  # Bunt
        }
        
        # Hotkey mappings for fielding positions in detail mode
        self.fielding_position_hotkeys = {
            '1': 1,  # Pitcher
            '2': 2,  # Catcher
            '3': 3,  # First base
            '4': 4,  # Second base
            '5': 5,  # Third base
            '6': 6,  # Shortstop
            '7': 7,  # Left field
            '8': 8,  # Center field
            '9': 9,  # Right field
        }
        
        # Hotkey mappings for out types in detail mode
        self.out_type_hotkeys = {
            'g': 'G',    # Ground out
            'l': 'L',    # Line out
            'f': 'F',    # Fly out
            'p': 'P',    # Pop out
            'b': 'B',    # Bunt out
            's': 'SF',   # Sacrifice fly
            'h': 'SH',   # Sacrifice hit/bunt
            'w': 'GDP',  # Grounded into double play
            '!': 'LDP',  # Lined into double play
            'y': 'TP',   # Triple play
            'z': 'FO',   # Force out
            '[': 'UO',   # Unassisted out
        }
        


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
                
                if key == 'q':
                    break
                elif key == 'left':
                    self._previous_play()
                elif key == 'right':
                    self._next_play()
                elif key == 'tab':  # Switch between modes
                    if self.mode == 'pitch':
                        self.mode = 'play'
                    elif self.mode == 'play':
                        # If current play already has a result, offer additional details
                        current_game = self.event_file.games[self.current_game_index]
                        if current_game.plays and current_game.plays[self.current_play_index].play_description:
                            self.mode = 'detail'
                            self._start_modifier_detail_mode()
                        else:
                            self.mode = 'detail'
                    elif self.mode == 'detail':
                        self.mode = 'pitch'  # Cycle back to pitch mode
                        self._reset_detail_mode()
                elif key == 'x':  # Undo last action
                    self._undo_last_action()
                elif key == '-':  # Clear (context-sensitive)
                    if self.mode == 'pitch':
                        self._clear_pitches()
                    elif self.mode == 'play':
                        self._clear_play_result()
                elif self.mode == 'pitch' and key in self.pitch_hotkeys:
                    self._add_pitch(self.pitch_hotkeys[key])
                elif self.mode == 'play' and key in self.play_hotkeys:
                    # Only certain results should enter detail mode
                    result = self.play_hotkeys[key]
                    if result == 'OUT' or result in ['S', 'D', 'T', 'HR', 'E', 'FC', 'SF', 'SH']:
                        # Generic out requires out-type/position details
                        # Hits, errors, and sacrifices require hit-type/position details
                        self._enter_detail_mode(result)
                    else:
                        # All other results should set immediately without entering detail mode
                        self._set_play_result(result)
                elif self.mode == 'detail':
                    if self.modifier_selection_active:
                        self._handle_modifier_mode_input(key)
                    else:
                        if key == '\r' or key == '\n':  # Enter key
                            # Allow saving multi-fielder plays with ENTER
                            if (self.detail_mode_result in ['OUT', 'GDP', 'LDP', 'TP', 'FO', 'UO'] and 
                                self.detail_mode_out_type and self.detail_mode_fielders):
                                self._save_detail_mode_result()
                        else:
                            self._handle_detail_mode_input(key)
                elif key == '\r' or key == '\n':  # Enter key
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
            Layout(name="controls", size=16)
        )
        
        # Header
        header = Panel(
            f"Game: {current_game.game_id} | "
            f"{current_game.info.away_team} @ {current_game.info.home_team} | "
            f"Date: {current_game.info.date}",
            title="Retrosheet Buddy",
            style="bold blue"
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
            style="bold reverse"
        )
        
        return Panel(table, title="Current Play")

    def _create_controls_panel(self) -> Panel:
        """Create the controls panel."""
        controls_text = Text()
        
        # Current mode indicator - dynamic text generation
        self._add_mode_section(controls_text)
        
        # Navigation - dynamic text generation
        self._add_navigation_section(controls_text)
        
        if self.mode == 'pitch':
            # Pitch controls - generated from pitch_hotkeys dictionary
            controls_text.append("Pitch Events:\n", style="bold green")
            self._add_hotkey_controls(controls_text, self.pitch_hotkeys, self._get_pitch_descriptions())
        elif self.mode == 'play':
            # Play results - generated from play_hotkeys dictionary
            controls_text.append("Play Results:\n", style="bold red")
            self._add_hotkey_controls(controls_text, self.play_hotkeys, self._get_play_descriptions())
        elif self.mode == 'detail':
            # Detail mode controls
            controls_text.append("Detail Mode:\n", style="bold yellow")
            # Additional modifiers selection UI
            if self.modifier_selection_active:
                if self.selected_modifier_group is None:
                    controls_text.append("Add Additional Details (optional):\n", style="bold green")
                    self._add_modifier_group_controls_wrapped(controls_text)
                    if self.selected_modifiers:
                        controls_text.append(f"Selected: {', '.join(self.selected_modifiers)}\n", style="bold cyan")
                    controls_text.append("Press the highlighted letter to choose a group, [ENTER] to apply and exit.\n", style="bold blue")
                else:
                    group_name, codes = self.modifier_groups[self.selected_modifier_group]
                    controls_text.append(f"{group_name}:\n", style="bold green")
                    if self.selected_modifier_group == 'h':
                        # Custom wizard UI for Hit Location
                        self._render_hit_location_builder(controls_text)
                    else:
                        # Render options in wrapped rows with max width, similar to other modes
                        self._add_modifier_options_wrapped(controls_text, codes)
                        if self.selected_modifiers:
                            controls_text.append(f"Selected: {', '.join(self.selected_modifiers)}\n", style="bold cyan")
                        if self.modifier_param_request:
                            if self.modifier_param_request['type'] == 'fielder':
                                controls_text.append("Enter fielder [1-9] for this modifier.\n", style="bold blue")
                            elif self.modifier_param_request['type'] == 'base':
                                controls_text.append("Enter base [1-4] for this modifier.\n", style="bold blue")
                        controls_text.append("Use letter keys to add, [0] to go back, [ENTER] to apply and exit.\n", style="bold blue")
            elif self.detail_mode_result:
                controls_text.append(f"Result: {self.detail_mode_result}\n", style="bold red")
                
                # Handle different types of plays
                if self.detail_mode_result in ['OUT', 'GDP', 'LDP', 'TP', 'FO', 'UO']:
                    # Out types need out type and fielding positions
                    if self.detail_mode_out_type is None:
                        controls_text.append("Out Type:\n", style="bold green")
                        self._add_hotkey_controls(controls_text, self.out_type_hotkeys, self._get_out_type_descriptions())
                        controls_text.append("Fielding Positions: [1-9] (multiple allowed)\n", style="bold blue")
                    elif not self.detail_mode_fielders:
                        controls_text.append(f"Out Type: {self.detail_mode_out_type}\n", style="bold green")
                        controls_text.append("Fielding Positions:\n", style="bold blue")
                        self._add_hotkey_controls(controls_text, self.fielding_position_hotkeys, self._get_fielding_position_descriptions())
                        controls_text.append("Select fielders sequentially (e.g., 6-4-3 for DP)\n", style="bold cyan")
                        controls_text.append("Press [ENTER] when done selecting fielders\n", style="bold cyan")
                    else:
                        controls_text.append(f"Out Type: {self.detail_mode_out_type}\n", style="bold green")
                        controls_text.append(f"Fielding Positions: {', '.join(map(str, self.detail_mode_fielders))}\n", style="bold blue")
                        controls_text.append("Fielding Positions:\n", style="bold blue")
                        self._add_hotkey_controls(controls_text, self.fielding_position_hotkeys, self._get_fielding_position_descriptions())
                        controls_text.append("Press [ENTER] to save or add more positions\n", style="bold cyan")
                else:
                    # Regular hits need hit type and fielding position
                    if self.detail_mode_hit_type is None:
                        controls_text.append("Hit Type:\n", style="bold green")
                        self._add_hotkey_controls(controls_text, self.hit_type_hotkeys, self._get_hit_type_descriptions())
                        controls_text.append("Fielding Position: [1-9]\n", style="bold blue")
                    elif not self.detail_mode_fielders:
                        controls_text.append(f"Hit Type: {self.detail_mode_hit_type}\n", style="bold green")
                        controls_text.append("Fielding Position:\n", style="bold blue")
                        self._add_hotkey_controls(controls_text, self.fielding_position_hotkeys, self._get_fielding_position_descriptions())
                    else:
                        controls_text.append(f"Hit Type: {self.detail_mode_hit_type}\n", style="bold green")
                        controls_text.append(f"Fielding Position: {self.detail_mode_fielders[0]}\n", style="bold blue")
                        controls_text.append("Press [ENTER] to save and exit detail mode.\n", style="bold cyan")
            else:
                controls_text.append("Select a play result to enter detail mode.\n", style="bold red")
        
        # Calculate the height of the generated text
        text_height = self._calculate_text_height(controls_text)
        
        # Add padding for panel borders and title (typically 3-4 lines)
        panel_height = text_height + 4
        
        return Panel(controls_text, title="Controls", height=panel_height)

    def _calculate_text_height(self, text: Text) -> int:
        """Calculate the height (number of lines) of a Text object."""
        # Convert Text to string and count lines
        text_str = str(text)
        lines = text_str.split('\n')
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
        mode_style = "bold green" if self.mode == 'pitch' else "bold red" if self.mode == 'play' else "bold yellow"
        controls_text.append(f"Current Mode: {self.mode.upper()}\n", style=mode_style)
        
        # Determine which mode TAB would switch to
        if self.mode == 'pitch':
            next_mode = 'play'
        elif self.mode == 'play':
            next_mode = 'detail'
        else:  # detail mode
            next_mode = 'pitch'
        
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
            "[Q] Quit",
            "[X] Undo last action"
        ]

        # Context-sensitive clear hint
        if self.mode == 'pitch':
            nav_items.append("[-] Clear pitches")
        elif self.mode == 'play':
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
        return {
            'B': 'Ball',
            'S': 'Swinging Strike',
            'F': 'Foul',
            'C': 'Called Strike',
            'T': 'Foul tip',
            'M': 'Missed bunt',
            'P': 'Pitchout',
            'I': 'Intentional ball',
            'H': 'Hit batter',
            'V': 'Wild pitch',
            'A': 'Passed ball',
            'Q': 'Swinging on pitchout',
            'R': 'Foul on pitchout',
            'E': 'Foul bunt',
            'N': 'No pitch',
            'O': 'Foul on bunt',
            'U': 'Unknown',
        }

    def _get_play_descriptions(self) -> dict:
        """Get descriptions for play results."""
        return {
            'S': 'Single',
            'D': 'Double', 
            'T': 'Triple',
            'HR': 'Home run',
            'K': 'Strikeout',
            'W': 'Walk',
            'HP': 'Hit by pitch',
            'E': 'Error',
            'FC': "Fielder's choice",
            'DP': 'Double play',
            'TP': 'Triple play',
            'SF': 'Sac fly',
            'SH': 'Sac bunt',
            'IW': 'Intentional walk',
            'CI': 'Catcher interference',
            'OA': 'Out advancing',
            'ND': 'No play',
            # New out types
            'OUT': 'Out',
            'GDP': 'Grounded into DP',
            'LDP': 'Lined into DP',
            'FO': 'Force out',
            'UO': 'Unassisted out',
        }

    def _get_hit_type_descriptions(self) -> dict:
        """Get descriptions for hit types."""
        return {
            'G': 'Grounder',
            'L': 'Line drive',
            'F': 'Fly ball',
            'P': 'Pop up',
            'B': 'Bunt',
        }

    def _get_fielding_position_descriptions(self) -> dict:
        """Get descriptions for fielding positions."""
        return {
            1: 'Pitcher',
            2: 'Catcher',
            3: 'First base',
            4: 'Second base',
            5: 'Third base',
            6: 'Shortstop',
            7: 'Left field',
            8: 'Center field',
            9: 'Right field',
        }

    def _get_out_type_descriptions(self) -> dict:
        """Get descriptions for out types in detail mode."""
        return {
            'G': 'Ground out',
            'L': 'Line out',
            'F': 'Fly out',
            'P': 'Pop out',
            'B': 'Bunt out',
            'SF': 'Sacrifice fly',
            'SH': 'Sacrifice hit/bunt',
            'GDP': 'Grounded into double play',
            'LDP': 'Lined into double play',
            'TP': 'Triple play',
            'FO': 'Force out',
            'UO': 'Unassisted out',
        }

    def _generate_retrosheet_play_description(self, result: str, fielding_position: int = 0) -> str:
        """Generate proper Retrosheet play description format."""
        if result == 'S':  # Single
            if fielding_position > 0:
                return f"S{fielding_position}/G{fielding_position}"
            return "S8/G6"  # Default to center field
        elif result == 'D':  # Double
            if fielding_position > 0:
                return f"D{fielding_position}/L{fielding_position}"
            return "D7/L7"  # Default to left field
        elif result == 'T':  # Triple
            if fielding_position > 0:
                return f"T{fielding_position}/L{fielding_position}"
            return "T8/L8"  # Default to center field
        elif result == 'HR':  # Home run
            return "HR/F7"  # Over left field fence
        elif result == 'K':  # Strikeout
            return "K"
        elif result == 'W':  # Walk
            return "W"
        elif result == 'HP':  # Hit by pitch
            return "HP"
        elif result == 'E':  # Error
            if fielding_position > 0:
                return f"E{fielding_position}/G{fielding_position}"
            return "E6/G6"  # Default to shortstop
        elif result == 'FC':  # Fielder's choice
            if fielding_position > 0:
                return f"FC{fielding_position}/G{fielding_position}"
            return "FC6/G6"
        elif result == 'DP':  # Double play
            return "DP/G6"
        elif result == 'TP':  # Triple play
            return "TP/G6"
        elif result == 'SF':  # Sacrifice fly
            if fielding_position > 0:
                return f"SF{fielding_position}/F{fielding_position}"
            return "SF8/F8"
        elif result == 'SH':  # Sacrifice bunt
            if fielding_position > 0:
                return f"SH{fielding_position}/G{fielding_position}"
            return "SH1/G1"
        elif result == 'IW':  # Intentional walk
            return "IW"
        elif result == 'CI':  # Catcher interference
            return "CI"
        elif result == 'OA':  # Out advancing
            return "OA"
        elif result == 'ND':  # No play
            return "ND"
        # New out types
        elif result == 'OUT':  # Generic out
            if fielding_position > 0:
                return f"G{fielding_position}"
            return "G6"
        elif result == 'GDP':  # Grounded into double play
            if fielding_position > 0:
                return f"G{fielding_position}/GDP/G{fielding_position}"
            return "G6/GDP/G6"
        elif result == 'LDP':  # Lined into double play
            if fielding_position > 0:
                return f"L{fielding_position}/LDP/L{fielding_position}"
            return "L6/LDP/L6"
        elif result == 'FO':  # Force out
            if fielding_position > 0:
                return f"G{fielding_position}/FO/G{fielding_position}"
            return "G6/FO/G6"
        elif result == 'UO':  # Unassisted out
            if fielding_position > 0:
                return f"G{fielding_position}/UO/G{fielding_position}"
            return "G6/UO/G6"
        else:
            return result

    def _add_hotkey_controls(self, controls_text: Text, hotkeys: dict, descriptions: dict) -> None:
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
            self.current_play_index -= 1

    def _next_play(self) -> None:
        """Go to next play."""
        current_game = self.event_file.games[self.current_game_index]
        if self.current_play_index < len(current_game.plays) - 1:
            self.current_play_index += 1

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

    def _calculate_count(self, pitches: str) -> str:
        """Calculate count from pitch sequence following baseball rules."""
        balls = 0
        strikes = 0
        
        for pitch in pitches:
            if pitch == 'B':
                balls += 1
            elif pitch in ['S', 'C']:  # Swinging strike, Called strike
                strikes += 1
            elif pitch == 'F':  # Foul ball
                # Foul balls only count as strikes up to 2 strikes
                if strikes < 2:
                    strikes += 1
            elif pitch == 'T':  # Foul tip
                # Foul tips count as strikes and can result in strikeout
                strikes += 1
            # Other pitch types (H, V, A, M, P, I, Q, R, E, N, O, U) don't affect count
        
        # Cap balls at 4 (walk) and strikes at 3 (strikeout)
        balls = min(balls, 4)
        strikes = min(strikes, 3)
        
        return f"{balls}{strikes}"

    def _add_pitch(self, pitch: str) -> None:
        """Add a pitch to the current play."""
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]
        
        # Save state before making changes
        self._save_state_for_undo()
        
        # Add pitch to the pitch sequence
        if current_play.pitches:
            current_play.pitches += pitch
        else:
            current_play.pitches = pitch
        
        # Update count (fouls count as strikes)
        current_play.count = self._calculate_count(current_play.pitches)
        # Mark as edited because pitches changed
        current_play.edited = True
        
        # Check for automatic walk or strikeout
        balls, strikes = int(current_play.count[0]), int(current_play.count[1])
        
        if balls == 4:
            # Automatic walk
            current_play.play_description = "W"
            current_play.edited = True
            self._save_current_state()
            # Move to next batter
            self._next_play()
        elif strikes == 3:
            # Automatic strikeout
            current_play.play_description = "K"
            current_play.edited = True
            self._save_current_state()
            # Move to next batter
            self._next_play()
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
            current_play.play_description
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
        current_play.count = self._calculate_count(current_play.pitches)
        
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
        current_play.count = self._calculate_count(current_play.pitches)
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
        self.mode = 'detail'

    def _handle_detail_mode_input(self, key: str) -> None:
        """Handle input in detail mode."""
        # Handle different types of plays
        if self.detail_mode_result in ['OUT', 'GDP', 'LDP', 'TP', 'FO', 'UO']:
            # Out types need out type and fielding positions
            if self.detail_mode_out_type is None and key in self.out_type_hotkeys:
                self.detail_mode_out_type = self.out_type_hotkeys[key]
            elif self.detail_mode_out_type is not None and key in self.fielding_position_hotkeys:
                # Add fielding position to the list
                self.detail_mode_fielders.append(self.fielding_position_hotkeys[key])
                
                # Don't automatically save - let user press ENTER when done selecting fielders
                # This allows for multi-fielder plays like 6-4-3 double plays
        else:
            # Regular hits need hit type and fielding position
            if key in self.hit_type_hotkeys:
                self.detail_mode_hit_type = self.hit_type_hotkeys[key]
            elif self.detail_mode_hit_type is not None and key in self.fielding_position_hotkeys:
                # For hits, we only need one fielding position
                self.detail_mode_fielders.append(self.fielding_position_hotkeys[key])
                
                # Automatically save and progress to next batter when both selections are complete
                if self.detail_mode_result and self.detail_mode_hit_type and self.detail_mode_fielders:
                    self._save_detail_mode_result()

    def _save_detail_mode_result(self) -> None:
        """Save the detailed play result and exit detail mode."""
        # Check if we have the required selections based on play type
        if self.detail_mode_result in ['OUT', 'GDP', 'LDP', 'TP', 'FO', 'UO']:
            # Out types need out type and fielding positions
            if self.detail_mode_result and self.detail_mode_out_type and self.detail_mode_fielders:
                # Generate the detailed play description
                play_description = self._generate_detailed_play_description(
                    self.detail_mode_result,
                    self.detail_mode_out_type,
                    self.detail_mode_fielders
                )
                
                # Set the play result
                current_game = self.event_file.games[self.current_game_index]
                current_play = current_game.plays[self.current_play_index]
                
                # Save state before making changes
                self._save_state_for_undo()
                
                current_play.play_description = play_description
                current_play.edited = True
                self._save_current_state()

                # After saving an out with fielders, automatically enter the
                # additional details selection inside detail mode so the user
                # can add modifiers immediately. Remain in detail mode.
                self._start_modifier_detail_mode()
            else:
                self.console.print("Please complete all detail selections", style="yellow")
        else:
            # Regular hits need hit type and fielding position
            if self.detail_mode_result and self.detail_mode_hit_type and self.detail_mode_fielders:
                # Generate the detailed play description
                play_description = self._generate_detailed_play_description(
                    self.detail_mode_result,
                    self.detail_mode_hit_type,
                    self.detail_mode_fielders[0]  # Use first fielder for hits
                )
                
                # Set the play result
                current_game = self.event_file.games[self.current_game_index]
                current_play = current_game.plays[self.current_play_index]
                
                # Save state before making changes
                self._save_state_for_undo()
                
                current_play.play_description = play_description
                current_play.edited = True
                self._save_current_state()
                
                # After saving main detail, optionally allow modifiers
                if self.selected_modifiers:
                    # Append modifiers to existing description
                    current_play.play_description += self._format_modifiers_suffix()
                    self._save_current_state()
                # Exit detail mode and return to pitch mode
                self.mode = 'pitch'
                self._reset_detail_mode()
                
                # Automatically progress to the next batter
                self._next_play()
            else:
                self.console.print("Please complete all detail selections", style="yellow")

    def _generate_detailed_play_description(self, result: str, hit_type: str, fielders) -> str:
        """Generate detailed Retrosheet play description with hit type and fielding positions."""
        # Handle fielders parameter - can be int (single) or list (multiple)
        if isinstance(fielders, int):
            fielding_position = fielders
            fielders_list = [fielders]
        else:
            fielding_position = fielders[0] if fielders else 0
            fielders_list = fielders
        
        if result == 'S':  # Single
            return f"S{fielding_position}/{hit_type}{fielding_position}"
        elif result == 'D':  # Double
            return f"D{fielding_position}/{hit_type}{fielding_position}"
        elif result == 'T':  # Triple
            return f"T{fielding_position}/{hit_type}{fielding_position}"
        elif result == 'HR':  # Home run
            return f"HR/{hit_type}{fielding_position}"
        elif result == 'E':  # Error
            return f"E{fielding_position}/{hit_type}{fielding_position}"
        elif result == 'FC':  # Fielder's choice
            return f"FC{fielding_position}/{hit_type}{fielding_position}"
        elif result == 'SF':  # Sacrifice fly
            return f"SF{fielding_position}/{hit_type}{fielding_position}"
        elif result == 'SH':  # Sacrifice bunt
            return f"SH{fielding_position}/{hit_type}{fielding_position}"
        elif result in ['OUT', 'GDP', 'LDP', 'TP', 'FO', 'UO']:
            # New formatting for outs: fielders first, then out type(s)
            out_type = hit_type  # may be base (G/L/F/P/B/SF/SH) or special (FO/UO/GDP/LDP/TP)
            fielder_string = ''.join(str(f) for f in fielders_list)

            tokens = [fielder_string] if fielder_string else [str(fielding_position)]

            # Always include the selected out_type if provided
            if out_type:
                tokens.append(out_type)

            # Append the specific result modifier if applicable and not duplicated
            if result in ['FO', 'UO', 'GDP', 'LDP', 'TP'] and result != out_type:
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
        if self.selected_modifier_group == 'h':
            if self._handle_hit_location_input(key):
                return

        # Finish and apply modifiers (only when not inside a wizard)
        if key in ['\r', '\n']:
            self._apply_modifiers_to_current_play()
            # Return to pitch mode after applying modifiers
            self.mode = 'pitch'
            self._reset_detail_mode()
            return

        # Back to group selection
        if key == '0':
            self.selected_modifier_group = None
            self.modifier_param_request = None
            self.current_modifier_options_keymap = {}
            return

        # If awaiting a parameter for a modifier
        if self.modifier_param_request:
            code = self.modifier_param_request['code']
            if self.modifier_param_request['type'] == 'fielder' and key in self.fielding_position_hotkeys:
                suffix = str(self.fielding_position_hotkeys[key])
                resolved = code.replace('$', suffix)
                self._append_modifier_to_current_play(resolved)
                self.modifier_param_request = None
            elif self.modifier_param_request['type'] == 'base' and key in ['1', '2', '3', '4']:
                resolved = code.replace('%', key)
                self._append_modifier_to_current_play(resolved)
                self.modifier_param_request = None
            return

        # Choose group
        if self.selected_modifier_group is None:
            if key in self.modifier_groups:
                self.selected_modifier_group = key
                # Initialize Hit Location builder state if chosen
                if key == 'h':
                    self.hit_location_active = True
                    self.hit_location_positions = ""
                    self.hit_location_suffix = ""
                    self.hit_location_depth = ""
            return

        # Choose option within group
        if key in self.current_modifier_options_keymap:
            code = self.current_modifier_options_keymap[key]
            # Codes that require parameter
            if code == 'E$':
                self.modifier_param_request = { 'code': 'E$', 'type': 'fielder' }
            elif code == 'R$':
                self.modifier_param_request = { 'code': 'R$', 'type': 'fielder' }
            elif code == 'TH%':
                self.modifier_param_request = { 'code': 'TH%', 'type': 'base' }
            else:
                self._append_modifier_to_current_play(code)
        # Any other key ignored

    def _render_hit_location_builder(self, controls_text: Text) -> None:
        """Render the Hit Location builder UI inside the modifiers panel."""
        # Positions
        pos_display = self.hit_location_positions or "(none)"
        controls_text.append("Positions (enter 1-2 digits [1-9]): ", style="bold blue")
        controls_text.append(f"{pos_display}\n")

        # M / L toggles based on positions
        allow_m = any(ch in ['4', '6'] for ch in self.hit_location_positions)
        # L only applies for exactly 7 or 9, not multi-position like 78 or 89
        allow_l = self.hit_location_positions in ['7', '9']

        if allow_m:
            m_state = "ON" if self.hit_location_suffix == 'M' else "OFF"
            controls_text.append("[M] Midfield (4/6 only): ", style="bold blue")
            controls_text.append(f"{m_state}\n", style="bold cyan")
        if allow_l:
            l_state = "ON" if self.hit_location_suffix == 'L' else "OFF"
            controls_text.append("[L] Near the foul line (7/9 only): ", style="bold blue")
            controls_text.append(f"{l_state}\n", style="bold cyan")

        # Foul territory toggle (for exact positions 2,3,5,7,9 or dual 23/25)
        allow_f = self.hit_location_positions in ['2', '3', '5', '7', '9', '23', '25']
        if allow_f:
            f_state = "ON" if self.hit_location_foul else "OFF"
            controls_text.append("[F] Foul territory (2/3/5/7/9 or 23/25): ", style="bold blue")
            controls_text.append(f"{f_state}\n", style="bold cyan")

        # Depth selection
        depth_display = self.hit_location_depth or "Normal"
        controls_text.append("Depth: [S] Shallow  [N] Normal  [D] Deep  [X] Extra Deep (XD)\n", style="bold blue")
        controls_text.append(f"Current: {depth_display}\n", style="bold cyan")

        # Instructions
        controls_text.append("[0] Back  [ENTER] Add to play\n", style="bold blue")

    def _handle_hit_location_input(self, key: str) -> bool:
        """Handle input for the Hit Location builder. Returns True if handled."""
        if not self.hit_location_active:
            return False

        # Back to group selection
        if key == '0':
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
        if key == 'm':
            if any(ch in ['4', '6'] for ch in self.hit_location_positions):
                self.hit_location_suffix = 'M' if self.hit_location_suffix != 'M' else ''
            return True

        # Toggle L (only when positions include 7 or 9)
        if key == 'l':
            if self.hit_location_positions in ['7', '9']:
                self.hit_location_suffix = 'L' if self.hit_location_suffix != 'L' else ''
            return True

        # Toggle F (only when positions are exactly 2,3,5,7,9, or dual 23/25)
        if key == 'f':
            if self.hit_location_positions in ['2', '3', '5', '7', '9', '23', '25']:
                self.hit_location_foul = not self.hit_location_foul
            return True

        # Depth selection
        if key == 's':
            self.hit_location_depth = 'S'
            return True
        if key == 'n':
            self.hit_location_depth = ''  # Normal depth has no code
            return True
        if key == 'd':
            self.hit_location_depth = 'D'
            return True
        if key == 'x':
            self.hit_location_depth = 'XD'
            return True

        # Apply on ENTER if valid
        if key in ['\r', '\n']:
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
                code += 'F'
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
        # Append directly without space or slash
        current_play.play_description += f"{code}"
        current_play.edited = True
        self._save_current_state()

    def _apply_modifiers_to_current_play(self) -> None:
        """Append selected modifiers to the current play description and save."""
        if self.modifiers_live_applied or not self.selected_modifiers:
            return
        current_game = self.event_file.games[self.current_game_index]
        current_play = current_game.plays[self.current_play_index]
        current_play.play_description = (current_play.play_description or '') + self._format_modifiers_suffix()
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
        if not current_play.play_description.endswith('/'):
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

        letter_ord = ord('a')
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