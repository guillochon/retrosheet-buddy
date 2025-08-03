# Retrosheet Buddy

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

### Interactive Controls

Retrosheet Buddy uses a **dual-mode system** to avoid keystroke conflicts between pitch events and play results. You can switch between modes using the **TAB** key.

#### Mode System

- **PITCH MODE** (default): For recording individual pitches
- **PLAY MODE**: For recording the final result of a play

Press **TAB** to switch between modes. The current mode is displayed at the top of the controls panel.

#### Navigation Keys

These work in both modes:

- **A** or **←**: Previous play
- **D** or **→**: Next play  
- **W** or **↑**: Previous game
- **S** or **↓**: Next game
- **Q**: Quit
- **X**: Undo last action
- **Enter**: Save current state

#### Pitch Mode Keystrokes

When in **PITCH MODE**, use these keys to record individual pitches:

| Key | Pitch Type | Description |
|-----|------------|-------------|
| **B** | Ball | Ball |
| **S** | Strike | Strike |
| **F** | Foul | Foul |
| **C** | Called Strike | Called strike |
| **W** | Swinging Strike | Swinging strike |
| **T** | Foul Tip | Foul tip |
| **M** | Missed Bunt | Missed bunt |
| **P** | Pitchout | Pitchout |
| **I** | Intentional Ball | Intentional ball |
| **H** | Hit Batter | Hit batter |
| **V** | Wild Pitch | Wild pitch |
| **A** | Passed Ball | Passed ball |
| **Q** | Swinging on Pitchout | Swinging on pitchout |
| **R** | Foul on Pitchout | Foul on pitchout |
| **E** | Foul Bunt | Foul bunt |
| **N** | No Pitch | No pitch |
| **O** | Foul on Bunt | Foul on bunt |
| **U** | Unknown | Unknown pitch |

#### Play Mode Keystrokes

When in **PLAY MODE**, use these keys to record the final result:

| Key | Result | Description |
|-----|--------|-------------|
| **1** | Single | Single |
| **2** | Double | Double |
| **3** | Triple | Triple |
| **4** | Home Run | Home run |
| **K** | Strikeout | Strikeout |
| **L** | Walk | Walk |
| **Y** | Hit by Pitch | Hit by pitch |
| **Z** | Error | Error |
| **G** | Fielder's Choice | Fielder's choice |
| **J** | Double Play | Double play |
| **5** | Triple Play | Triple play |
| **6** | Sacrifice Fly | Sacrifice fly |
| **7** | Sacrifice Bunt | Sacrifice bunt |
| **8** | Intentional Walk | Intentional walk |
| **9** | Catcher Interference | Catcher interference |
| **0** | Out Advancing | Out advancing |
| **;** | No Play | No play |

#### Workflow Example

Here's how to record a typical at-bat:

1. **Start in PITCH MODE** (default)
2. Press **S** to record a strike
3. Press **B** to record a ball  
4. Press **F** to record a foul
5. Press **S** to record another strike (strikeout)
6. Press **TAB** to switch to PLAY MODE
7. Press **K** to record the strikeout result
8. Press **Enter** to save

**Note**: Use **X** to undo any mistake, and **TAB** to switch between recording pitches and play results.

#### Troubleshooting

**Strike Key Not Working?**
The strike key **S** should work properly in **PITCH MODE**. If it's not working:
1. Make sure you're in **PITCH MODE** (check the mode indicator)
2. Press **TAB** to switch to PITCH MODE if needed
3. The **S** key should add a strike to the pitch sequence

**Key Conflicts Resolved**
Previously, there were conflicts between pitch and play keystrokes. This has been resolved by:
- Using different keys for play results (e.g., **L** for walk instead of **W**)
- Implementing the mode system to separate pitch and play functionality
- Ensuring no key is used for both pitch events and play results

**Testing Your Keystrokes**
Run the test script to verify all keystrokes work:

```bash
python test_keystrokes_simple.py
```

This will test all keystroke mappings and confirm there are no conflicts.

#### Tips

- **Always check the mode indicator** before pressing keys
- **Use TAB frequently** to switch between modes as needed
- **Save regularly** with the Enter key
- **Practice with the test script** to get familiar with the keystrokes
- **Remember the new play result keys** (L for walk, Y for hit by pitch, etc.)

#### Key Changes from Previous Version

- **S** now only works for strikes in PITCH MODE
- **W** now only works for swinging strikes in PITCH MODE  
- **L** is used for walks in PLAY MODE
- **Y** is used for hit by pitch in PLAY MODE
- **TAB** key added for mode switching
- **X** key added for undo functionality
- **"In play"** removed from pitch mode (use TAB to switch to play mode instead)
- All conflicts have been resolved

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