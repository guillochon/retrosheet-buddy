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

Retrosheet Buddy uses a **three-mode system** to avoid keystroke conflicts between pitch events and play results. You can cycle through modes using the **TAB** key.

#### Mode System

- **PITCH MODE** (default): For recording individual pitches
- **PLAY MODE**: For recording the final result of a play (including outs)
- **DETAIL MODE**: For specifying hit type and fielding position after selecting a play result

Press **TAB** to cycle through modes: PITCH → PLAY → DETAIL → PITCH. The current mode and next mode are displayed at the top of the controls panel.

#### Navigation Keys

These work in both modes:

- **A** or **←**: Previous play
- **D** or **→**: Next play  
- **W** or **↑**: Previous game
- **S** or **↓**: Next game
- **Q**: Quit
- **X**: Undo last action
- **-**: Clear (pitches in PITCH mode; result in PLAY mode)

#### Pitch Mode Keystrokes

When in **PITCH MODE**, use these keys to record individual pitches:

| Key | Pitch Type | Description |
|-----|------------|-------------|
| **B** | Ball | Ball |
| **S** | Swinging Strike | Swinging strike |
| **F** | Foul | Foul |
| **C** | Called Strike | Called strike |
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
| **W** | OUT | Generic out |
| **X** | GDP | Grounded into double play |
| **D** | LDP | Lined into double play |
| **[** | FO | Force out |
| **]** | UO | Unassisted out |

#### Detail Mode Keystrokes

When in **DETAIL MODE** (entered automatically after selecting a play result), you can specify:

**For hits and regular plays - Hit Type** (first selection):
| Key | Hit Type | Description |
|-----|----------|-------------|
| **G** | Grounder | Ground ball |
| **L** | Line Drive | Line drive |
| **F** | Fly Ball | Fly ball |
| **P** | Pop Up | Pop up |
| **B** | Bunt | Bunt |

**Fielding Position** (second selection):
| Key | Position | Description |
|-----|----------|-------------|
| **1** | Pitcher | Pitcher |
| **2** | Catcher | Catcher |
| **3** | First Base | First base |
| **4** | Second Base | Second base |
| **5** | Third Base | Third base |
| **6** | Shortstop | Shortstop |
| **7** | Left Field | Left field |
| **8** | Center Field | Center field |
| **9** | Right Field | Right field |

**Note**: For multi-fielder plays (like double plays), you can enter multiple positions in sequence. For example, for a 6-4-3 double play, you would enter **6**, then **4**, then **3**.

**For outs - Out Type** (first selection):
| Key | Out Type | Description |
|-----|----------|-------------|
| **G** | Ground Out | Ground out |
| **L** | Line Out | Line out |
| **F** | Fly Out | Fly out |
| **P** | Pop Out | Pop out |
| **B** | Bunt Out | Bunt out |
| **S** | Sacrifice Fly | Sacrifice fly |
| **H** | Sacrifice Hit/Bunt | Sacrifice hit/bunt |
| **W** | Grounded into DP | Grounded into double play |
| **X** | Lined into DP | Lined into double play |
| **Y** | Triple Play | Triple play |
| **Z** | Force Out | Force out |
| **[** | Unassisted Out | Unassisted out |

After selecting both hit type/out type and fielding position, the detailed play result is automatically saved, the editor progresses to the next batter, and returns to pitch mode.

#### Workflow Example

Here's how to record a typical at-bat:

1. **Start in PITCH MODE** (default)
2. Press **C** to record a called strike
3. Press **B** to record a ball  
4. Press **F** to record a foul
5. Press **S** to record a swinging strike (strikeout), buddy switches automatically to PLAY mode
6. Press **K** to record the strikeout result

**For detailed play results** (like hits):
1. In **PLAY MODE**, press **1** to select a single
2. Automatically enters **DETAIL MODE**
3. Press **G** to specify it's a grounder
4. Press **6** to specify it was fielded by the shortstop
5. Automatically saves the result as "S6/G6" (single to shortstop, grounder), progresses to the next batter, and returns to pitch mode

**For out types**:
1. In **PLAY MODE**, press **W** to select a generic out
2. Automatically enters **DETAIL MODE**
3. Press **G** to specify it's a ground out
4. Press **6** to specify it was fielded by the shortstop
5. Automatically saves the result as "6/G" (fielder then out type), progresses to the next batter, and returns to pitch mode

**For double plays**:
1. In **PLAY MODE**, press **X** to select "Grounded into double play"
2. Automatically enters **DETAIL MODE**
3. Press **G** to specify it's a ground out
4. Press **6** to specify it was fielded by the shortstop
5. Automatically saves the result as "6/G/GDP" (fielder then out type and DP modifier), progresses to the next batter, and returns to pitch mode

**For multi-fielder plays**:
1. In **PLAY MODE**, press **X** to select "Grounded into double play"
2. Automatically enters **DETAIL MODE**
3. Press **G** to specify it's a ground out
4. Press **6** to specify the shortstop fielded it
5. Press **4** to specify the second baseman received the throw
6. Press **3** to specify the first baseman received the final throw
7. Automatically saves the result as "643/G/GDP" (fielders first, then out type and DP), progresses to the next batter, and returns to pitch mode

**Note**: Use **X** to undo any mistake, and **TAB** to cycle through modes (PITCH → PLAY → DETAIL → PITCH).

#### Tips

- **Always check the mode indicator** before pressing keys
- **Use TAB frequently** to cycle through modes as needed
- **Practice with the test script** to get familiar with the keystrokes

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