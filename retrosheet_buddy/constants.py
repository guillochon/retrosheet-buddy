"""Constants and static dictionaries for the Retrosheet editor."""

# Navigation shortcuts (work in all modes)
NAVIGATION_SHORTCUTS = {
    "q": "Quit",
    "left": "Previous play",
    "right": "Next play",
    "down": "Next incomplete play",
    "tab": "Switch modes",
    "x": "Undo last action",
    "-": "Clear (pitches in PITCH mode, result in PLAY mode)",
    "j": "Jump to play",
    "\r": "Enter key",
    "\n": "Enter key",
}

# Mode shortcuts for validation
PITCH_SHORTCUTS = {
    "b": "Ball",
    "s": "Swinging strike",
    "f": "Foul",
    "c": "Called strike",
    "t": "Foul tip",
    "m": "Missed bunt",
    "p": "Pitchout",
    "i": "Intentional ball",
    "h": "Hit batter",
    "v": "Wild pitch",
    "a": "Passed ball",
    "*": "Swinging on pitchout",
    "r": "Foul on pitchout",
    "e": "Foul bunt",
    "n": "No pitch",
    "o": "Foul on bunt",
    "k": "Pick off attempt",
    ".": "Ball in play (append X & switch)",
    "u": "Unknown",
}

PLAY_SHORTCUTS = {
    "w": "Out",
    "1": "Single",
    "2": "Double",
    "3": "Triple",
    "4": "Home run",
    "l": "Walk",
    "y": "Hit by pitch",
    "z": "Error",
    "8": "Intentional walk",
    "9": "Catcher interference",
    "0": "Out advancing",
    ";": "No play",
    "f": "Sacrifice fly",
    "k": "Sacrifice hit/bunt",
}

# Detail mode shortcuts (only active in detail mode)
HIT_TYPE_SHORTCUTS = {
    "g": "Grounder",
    "l": "Line drive",
    "f": "Fly ball",
    "p": "Pop up",
    "b": "Bunt",
}

FIELDING_POSITION_SHORTCUTS = {
    "1": "Pitcher",
    "2": "Catcher",
    "3": "First base",
    "4": "Second base",
    "5": "Third base",
    "6": "Shortstop",
    "7": "Left field",
    "8": "Center field",
    "9": "Right field",
}

OUT_TYPE_SHORTCUTS = {
    "g": "Ground out",
    "l": "Line out",
    "f": "Fly out",
    "p": "Pop out",
    "b": "Bunt out",
    "s": "Sacrifice fly",
    "h": "Sacrifice hit/bunt",
    "k": "Strikeout",
    "c": "Fielder's choice",
    "d": "Double play",
    "w": "Grounded into double play",
    "!": "Lined into double play",
    "y": "Triple play",
    "z": "Force out",
    "[": "Unassisted out",
}

# Hotkey mappings for pitch events (no conflicts).
# This dictionary determines the order that the pitch events are displayed in the controls panel.
PITCH_HOTKEYS = {
    "b": "B",  # Ball
    "s": "S",  # Swinging strike
    "f": "F",  # Foul
    "c": "C",  # Called strike
    "t": "T",  # Foul tip
    "m": "M",  # Missed bunt
    "p": "P",  # Pitchout
    "i": "I",  # Intentional ball
    "h": "H",  # Hit batter
    "v": "V",  # Wild pitch
    "a": "A",  # Passed ball
    "*": "Q",  # Swinging on pitchout
    "r": "R",  # Foul on pitchout
    "e": "E",  # Foul bunt
    "n": "N",  # No pitch
    "o": "O",  # Foul on bunt
    "k": "PK",  # Pick off attempt
    ".": "X",  # Ball in play: append X and switch to play mode
    "u": "U",  # Unknown
}

# Hotkey mappings for play results (consolidated to avoid duplication)
# Out-related results are selected via the Out Type wizard after choosing OUT
# This dictionary determines the order that the play results are displayed in the controls panel.
PLAY_HOTKEYS = {
    "o": "OUT",  # Out
    "1": "S",  # Single
    "2": "D",  # Double
    "3": "T",  # Triple
    "4": "HR",  # Home run
    "p": "PO",  # Pickoff
    "c": "POCS",  # Pickoff caught stealing
    "t": "CS",  # Caught stealing
    "b": "BK",  # Balk (runner advances)
    "d": "DI",  # Defensive indifference
    "a": "PB",  # Passed ball
    "w": "WP",  # Wild pitch
    "s": "SB",  # Stolen base
    "l": "W",  # Walk
    "h": "HP",  # Hit by pitch
    "e": "E",  # Error
    "i": "IW",  # Intentional walk
    "j": "CI",  # Catcher interference
    "0": "OA",  # Out advancing
    ";": "ND",  # No play
    "f": "SF",  # Sacrifice fly
    "k": "SH",  # Sacrifice hit/bunt
}

# Hotkey mappings for hit types in detail mode
HIT_TYPE_HOTKEYS = {
    "g": "G",  # Grounder
    "l": "L",  # Line drive
    "f": "F",  # Fly ball
    "p": "P",  # Pop up
    "b": "B",  # Bunt
}

# Hotkey mappings for fielding positions in detail mode
FIELDING_POSITION_HOTKEYS = {
    "1": 1,  # Pitcher
    "2": 2,  # Catcher
    "3": 3,  # First base
    "4": 4,  # Second base
    "5": 5,  # Third base
    "6": 6,  # Shortstop
    "7": 7,  # Left field
    "8": 8,  # Center field
    "9": 9,  # Right field
}

# Hotkey mappings for out types in detail mode
OUT_TYPE_HOTKEYS = {
    "g": "G",  # Ground out
    "l": "L",  # Line out
    "f": "F",  # Fly out
    "p": "P",  # Pop out
    "b": "B",  # Bunt out
    "s": "SF",  # Sacrifice fly
    "h": "SH",  # Sacrifice hit/bunt
    "k": "K",  # Strikeout
    "c": "FC",  # Fielder's choice
    "d": "DP",  # Double play (generic)
    "w": "GDP",  # Grounded into double play
    "!": "LDP",  # Lined into double play
    "y": "TP",  # Triple play
    "z": "FO",  # Force out
    "[": "UO",  # Unassisted out
}

# Modifier descriptions for play details
MODIFIER_DESCRIPTIONS = {
    # Bunt-related
    "BP": "Bunt pop up",
    "BG": "Ground ball bunt",
    "BGDP": "Bunt grounded into double play",
    "BL": "Line drive bunt",
    "BPDP": "Bunt popped into double play",
    "SH": "Sacrifice hit (bunt)",
    # Ball type / plays
    "G": "Ground ball",
    "L": "Line drive",
    "F": "Fly ball",
    "P": "Pop fly",
    "FL": "Foul",
    "IF": "Infield fly rule",
    "DP": "Unspecified double play",
    "TP": "Unspecified triple play",
    "GDP": "Ground ball double play",
    "GTP": "Ground ball triple play",
    "LDP": "Lined into double play",
    "LTP": "Lined into triple play",
    "NDP": "No double play credited for this play",
    "SF": "Sacrifice fly",
    "FO": "Force out",
    # Interference/obstruction
    "BINT": "Batter interference",
    "INT": "Interference",
    "RINT": "Runner interference",
    "UINT": "Umpire interference",
    "OBS": "Obstruction (fielder obstructing a runner)",
    "FINT": "Fan interference",
    # Administrative / courtesy / reviews / misc
    "AP": "Appeal play",
    "C": "Called third strike",
    "COUB": "Courtesy batter",
    "COUF": "Courtesy fielder",
    "COUR": "Courtesy runner",
    "MREV": "Manager challenge of call on the field",
    "UREV": "Umpire review of call on the field",
    "BOOT": "Batting out of turn",
    "IPHR": "Inside the park home run",
    "PASS": "Runner passed another runner and was called out",
    "BR": "Runner hit by batted ball",
    "TH": "Throw",
    "TH%": "Throw to base %",
    "R$": "Relay throw from initial fielder to $",
    "E$": "Error on $",
}

# Modifier groups for organizing play details
MODIFIER_GROUPS = {
    # Note: '0' is reserved for "back" in modifier UI; use mnemonic letters for groups
    "b": ("Ball Types", ["G", "L", "F", "P", "FL", "IF"]),
    "s": ("Sacrifices", ["SF", "SH"]),
    "u": (
        "Bunt Types",
        ["BP", "BG", "BL"],
    ),  # 'u' for bUnt to avoid collision with Ball Types
    "d": ("DP/TP (Generic)", ["DP", "TP"]),
    "v": (
        "DP/TP Variants",
        ["GDP", "GTP", "LDP", "LTP", "NDP", "BGDP", "BPDP"],
    ),
    "i": (
        "Interference/Obstruction",
        ["BINT", "INT", "RINT", "FINT", "UINT", "OBS"],
    ),
    "a": (
        "Administrative",
        ["AP", "BOOT", "C", "IPHR", "PASS", "BR", "MREV", "UREV"],
    ),
    "c": ("Courtesy", ["COUB", "COUF", "COUR"]),
    "t": ("Throws/Relays", ["TH", "TH%", "R$"]),
    "e": ("Errors", ["E$"]),
    "h": ("Hit Location", []),
    "r": ("Advance Runner", []),
}

# Description dictionaries for UI display
PITCH_DESCRIPTIONS = {
    "B": "Ball",
    "S": "Swinging Strike",
    "F": "Foul",
    "C": "Called Strike",
    "T": "Foul tip",
    "M": "Missed bunt",
    "P": "Pitchout",
    "I": "Intentional ball",
    "H": "Hit batter",
    "V": "Wild pitch",
    "A": "Passed ball",
    "Q": "Swinging on pitchout",
    "R": "Foul on pitchout",
    "E": "Foul bunt",
    "N": "No pitch",
    "O": "Foul on bunt",
    "PK": "Pick off attempt",
    "X": "Ball in play",
    "U": "Unknown",
}

PLAY_DESCRIPTIONS = {
    "S": "Single",
    "D": "Double",
    "T": "Triple",
    "HR": "Home run",
    "W": "Walk",
    "HP": "Hit by pitch",
    "E": "Error",
    "SF": "Sacrifice fly",
    "SH": "Sacrifice hit/bunt",
    # Out-type wizard items (selected after OUT)
    "K": "Strikeout",
    "FC": "Fielder's choice",
    "DP": "Double play",
    "TP": "Triple play",
    "IW": "Intentional walk",
    "CI": "Catcher interference",
    "OA": "Out advancing",
    "ND": "No play",
    # New out types
    "OUT": "Out",
    "GDP": "Grounded into DP",
    "LDP": "Lined into DP",
    "FO": "Force out",
    "UO": "Unassisted out",
    "PO": "Pickoff",
    "POCS": "Pickoff - Caught Stealing",
    "CS": "Caught Stealing",
    "BK": "Balk",
    "DI": "Defensive indifference",
    "PB": "Passed ball",
    "WP": "Wild pitch",
    "SB": "Stolen base",
}

HIT_TYPE_DESCRIPTIONS = {
    "G": "Grounder",
    "L": "Line drive",
    "F": "Fly ball",
    "P": "Pop up",
    "B": "Bunt",
}

FIELDING_POSITION_DESCRIPTIONS = {
    1: "Pitcher",
    2: "Catcher",
    3: "First base",
    4: "Second base",
    5: "Third base",
    6: "Shortstop",
    7: "Left field",
    8: "Center field",
    9: "Right field",
}

OUT_TYPE_DESCRIPTIONS = {
    "G": "Ground out",
    "L": "Line out",
    "F": "Fly out",
    "P": "Pop out",
    "B": "Bunt out",
    "SF": "Sacrifice fly",
    "SH": "Sacrifice hit/bunt",
    "K": "Strikeout",
    "FC": "Fielder's choice",
    "DP": "Double play",
    "GDP": "Grounded into double play",
    "LDP": "Lined into double play",
    "TP": "Triple play",
    "FO": "Force out",
    "UO": "Unassisted out",
}

# Combined detail mode shortcuts for validation
DETAIL_MODE_SHORTCUTS = {
    **HIT_TYPE_SHORTCUTS,
    **FIELDING_POSITION_SHORTCUTS,
    **OUT_TYPE_SHORTCUTS,
}
