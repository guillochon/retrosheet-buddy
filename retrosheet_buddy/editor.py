"""Interactive editor for Retrosheet event files."""

import platform
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import EventFile, Game
from .parser import parse_event_file
from .writer import write_event_file


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
        self.mode = 'pitch'  # 'pitch' or 'play'
        
        # Undo functionality
        self.undo_history = []  # List of (game_index, play_index, pitches, play_description) tuples
        
        # Hotkey mappings for pitch events (no conflicts)
        self.pitch_hotkeys = {
            'b': 'B',  # Ball
            's': 'S',  # Strike
            'f': 'F',  # Foul
            'c': 'C',  # Called strike
            'w': 'W',  # Swinging strike
            't': 'T',  # Foul tip
            'm': 'M',  # Missed bunt
            'p': 'P',  # Pitchout
            'i': 'I',  # Intentional ball
            'h': 'H',  # Hit batter
            'v': 'V',  # Wild pitch
            'a': 'A',  # Passed ball
            'q': 'Q',  # Swinging on pitchout
            'r': 'R',  # Foul on pitchout
            'e': 'E',  # Foul bunt
            'n': 'N',  # No pitch
            'o': 'O',  # Foul on bunt
            'u': 'U',  # Unknown
        }
        
        # Hotkey mappings for play results (using different keys to avoid conflicts)
        self.play_hotkeys = {
            '1': 'S1',  # Single
            '2': 'D2',  # Double
            '3': 'T3',  # Triple
            '4': 'HR',  # Home run
            'k': 'K',   # Strikeout
            'l': 'W',   # Walk (changed from 'w')
            'y': 'HP',  # Hit by pitch (changed from 'h')
            'z': 'E',   # Error (changed from 'e')
            'g': 'FC',  # Fielder's choice (changed from 'f')
            'j': 'DP',  # Double play (changed from 'd')
            '5': 'TP',  # Triple play (changed from 't')
            '6': 'SF',  # Sacrifice fly (changed from 's')
            '7': 'SH',  # Sacrifice bunt (changed from 'b')
            '8': 'IW',  # Intentional walk (changed from 'i')
            '9': 'CI',  # Catcher interference (changed from 'c')
            '0': 'OA',  # Out advancing (changed from 'o')
            ';': 'ND',  # No play (changed from 'n')
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
                elif key == 'left' or key == 'a':
                    self._previous_play()
                elif key == 'right' or key == 'd':
                    self._next_play()
                elif key == 'tab':  # Switch between pitch and play modes
                    self.mode = 'play' if self.mode == 'pitch' else 'pitch'
                elif key == 'x':  # Undo last action
                    self._undo_last_action()
                elif self.mode == 'pitch' and key in self.pitch_hotkeys:
                    self._add_pitch(self.pitch_hotkeys[key])
                elif self.mode == 'play' and key in self.play_hotkeys:
                    self._set_play_result(self.play_hotkeys[key])
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
        else:
            # Play results - generated from play_hotkeys dictionary
            controls_text.append("Play Results:\n", style="bold red")
            self._add_hotkey_controls(controls_text, self.play_hotkeys, self._get_play_descriptions())
        
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
        mode_style = "bold green" if self.mode == 'pitch' else "bold red"
        controls_text.append(f"Current Mode: {self.mode.upper()}\n", style=mode_style)
        
        # Mode switch instruction
        mode_switch_text = "  [TAB] Switch modes"
        if len(mode_switch_text) <= available_width:
            controls_text.append(mode_switch_text + "\n\n")
        else:
            # Split if needed (though unlikely for this short text)
            controls_text.append("  [TAB] Switch\n  modes\n\n")

    def _add_navigation_section(self, controls_text: Text) -> None:
        """Add the navigation section with dynamic text generation."""
        # Calculate maximum width: minimum of console width and 120 characters
        max_width = min(self.console.width, 120)
        
        # Account for indentation (2 spaces)
        available_width = max_width - 2
        
        controls_text.append("Navigation:\n", style="bold cyan")
        
        # Navigation items
        nav_items = [
            "[A] Previous play",
            "[D] Next play", 
            "[Q] Quit",
            "[X] Undo last action"
        ]
        
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
            'S': 'Called Strike',
            'F': 'Foul',
            'C': 'Called',
            'W': 'Swinging',
            'T': 'Foul tip',
            'H': 'Hit batter',
            'V': 'Wild pitch',
            'A': 'Passed ball',
            'M': 'Missed bunt',
            'P': 'Pitchout',
            'I': 'Intentional ball',
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
            'S1': 'Single',
            'D2': 'Double',
            'T3': 'Triple',
            'HR': 'HR',
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
        }

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
            elif pitch in ['S', 'C', 'W']:  # Regular strikes
                strikes += 1
            elif pitch == 'F':  # Foul ball
                # Foul balls only count as strikes up to 2 strikes
                if strikes < 2:
                    strikes += 1
            # Other pitch types (T, H, V, A, M, P, I) don't affect count
        
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
        
        # Check for automatic walk or strikeout
        balls, strikes = int(current_play.count[0]), int(current_play.count[1])
        
        if balls == 4:
            # Automatic walk
            current_play.play_description = "W"
            self._save_current_state()
            # Move to next batter
            self._next_play()
        elif strikes == 3:
            # Automatic strikeout
            current_play.play_description = "K"
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
        
        current_play.play_description = result
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
        
        # Update count (fouls count as strikes)
        current_play.count = self._calculate_count(current_play.pitches)
        
        self.console.print("Undo completed", style="green")
        self._save_current_state()


def run_editor(event_file_path: Path, output_dir: Path) -> None:
    """Run the interactive editor."""
    try:
        event_file = parse_event_file(event_file_path)
        editor = RetrosheetEditor(event_file, output_dir)
        editor.run()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1) 