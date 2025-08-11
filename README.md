# Retrosheet Buddy

[![CI](https://github.com/guillochon/retrosheet-buddy/actions/workflows/ci.yml/badge.svg)](https://github.com/guillochon/retrosheet-buddy/actions/workflows/ci.yml)

An interactive command line editor for Retrosheet event files. This tool allows you to edit play-by-play data from baseball games using single keystroke commands.

## Features

- **Interactive Editing**: Edit Retrosheet event files with single keystroke commands (no Enter required)
- **Real-time Saving**: Changes are automatically saved to disk as you make them
- **Rich Interface**: Beautiful terminal interface with clear navigation and controls
- **Pitch-by-Pitch Recording**: Record individual pitches and play results
- **Game Navigation**: Jump between games and plays easily
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

This project uses `uv` for package management. To install:

```bash
# Clone the repository
git clone <repository-url>
cd retrosheet-buddy

# Install dependencies
uv sync

# Install the package in development mode
uv pip install -e .
```

## Usage

### Basic Usage

```bash
# Edit an existing event file
retrosheet-buddy path/to/your/file.EVN

# Specify a custom output directory
retrosheet-buddy path/to/your/file.EVN --output-dir ./my-outputs
```

### Modes and flow

Retrosheet Buddy uses three modes. Press TAB to cycle: PITCH → PLAY → DETAIL → PITCH. The current and next mode are shown in the on-screen panel.

- PITCH mode: record individual pitches
- PLAY mode: choose the final result of the play
- DETAIL mode: add hit/out type and fielders (auto-entered after a result that needs detail)

### Quick examples

- Auto strikeout from pitches:
  - PITCH: C, C, S → auto: K; advances to next batter

- Auto walk from pitches:
  - PITCH: B, B, B, B → auto: W; advances to next batter

- Normal pitch sequence (no result yet):
  - PITCH: B, S, F, B → count 22; stays on batter

- Single, grounder to shortstop:
  - PLAY: 1 → DETAIL: g, 6 → auto-saved as S6/G6; returns to PITCH

- Double to left, line drive:
  - PLAY: 2 → DETAIL: l, 7 → auto-saved as D7/L7; returns to PITCH

- Groundout 6-3 (generic OUT):
  - PLAY: w (OUT) → DETAIL: g, 6, 3 → press Enter to save as 63/G; press TAB to return to PITCH

- Grounded into DP 6-4-3:
  - PLAY: w (OUT) → DETAIL: w (GDP), g, 6, 4, 3 → press Enter to save as 643/G/GDP; press TAB to return to PITCH

Tip: Hits auto-save after selecting fielding; OUT/GDP/LDP require Enter to save. The in-app controls panel shows the full shortcut reference and current mode.

## Retrosheet Event File Format

This tool works with Retrosheet event files, which contain detailed play-by-play data for baseball games. The format is described in detail at [Retrosheet's Event File documentation](https://www.retrosheet.org/eventfile.htm).

### Game ID Format

Game IDs follow the format: `TTTYYYYMMDDN` where:
- `TTT` = Three-character team code
- `YYYY` = Four-digit year
- `MM` = Two-digit month
- `DD` = Two-digit day
- `N` = Game number (0 for single game, 1 for first game of doubleheader, etc.)

Example: `ATL198304080` represents the Atlanta Braves game on April 8, 1983.

## Development

### Project Structure

```
retrosheet-buddy/
├── retrosheet_buddy/
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── models.py        # Data models
│   ├── parser.py        # Event file parser
│   ├── writer.py        # Event file writer
│   └── editor.py        # Interactive editor
├── pyproject.toml       # Project configuration
└── README.md
```

### Running Tests

```bash
uv run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Retrosheet](https://www.retrosheet.org/) for the event file format specification
- [Rich](https://rich.readthedocs.io/) for the beautiful terminal interface
- [Click](https://click.palletsprojects.com/) for the CLI framework 