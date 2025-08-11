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

- Strikeout from pitches:
  - PITCH: C, F, S → auto-switches to PLAY
  - PLAY: K

- Single to center on a line drive:
  - PLAY: 1 → DETAIL: L, 8 → saved; returns to PITCH

- Groundout 6-3:
  - PLAY: W → DETAIL: G, 6, 3 → saved; returns to PITCH

- 6-4-3 double play:
  - PLAY: X → DETAIL: G, 6, 4, 3 → saved; returns to PITCH

- Walk:
  - PLAY: L → saved; returns to PITCH

Tip: Refer to the in-app controls panel for the full shortcut reference and current mode.

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

### Code Formatting

```bash
uv run black .
uv run isort .
```

## Current Status

✅ **Complete and Working**
- All core functionality implemented
- Tests passing
- Sample data included
- Documentation complete
- Ready for use

## Limitations

- Creating new event files from game IDs is not yet implemented
- The pitch count calculation is simplified and may not handle all edge cases
- Advanced Retrosheet features like replay reviews and ejections are not yet supported

## Future Enhancements

- Game ID to new file creation
- More advanced pitch count logic
- Support for replay reviews and ejections
- Batch processing of multiple files
- Export to other formats
- Undo/redo functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Retrosheet](https://www.retrosheet.org/) for the event file format specification
- [Rich](https://rich.readthedocs.io/) for the beautiful terminal interface
- [Click](https://click.palletsprojects.com/) for the CLI framework 