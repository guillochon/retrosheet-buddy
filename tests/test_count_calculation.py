"""Tests for count calculation functionality."""

import pytest


def calculate_count(pitches: str) -> str:
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


@pytest.mark.parametrize("pitches,expected", [
    ("", "00"),
    ("B", "10"),
    ("S", "01"),
    ("BB", "20"),
    ("SS", "02"),
    ("BS", "11"),
    ("BBF", "21"),  # 2 balls, 1 strike (foul counts as strike)
    ("BBFS", "22"),  # 2 balls, 2 strikes
    ("BBFSS", "23"),  # 2 balls, 3 strikes (strikeout)
    ("BBFSSS", "23"),  # 2 balls, 3 strikes (strikeout)
    ("BBFSSSB", "33"),  # 3 balls, 3 strikes
    ("BBFSSSBB", "43"),  # 4 balls, 3 strikes
    ("BBFSSSBBB", "43"),  # 5 balls, 3 strikes = 4 balls (capped), 3 strikes
    ("BBFSSSBBBB", "43"),  # 6 balls, 3 strikes = 4 balls (capped), 3 strikes
    ("BFFFFF", "12"),  # 1 ball, 5 fouls = 1 ball, 2 strikes (fouls only count up to 2)
    ("BBBBBBBB", "40"),  # 8 balls = 4 balls (capped at 4 for walk)
    ("SSS", "03"),  # 3 strikes (strikeout)
    ("SSF", "02"),  # 2 strikes, 1 foul = 2 strikes (foul doesn't count after 2 strikes)
    ("SSFF", "02"),  # 2 strikes, 2 fouls = 2 strikes (fouls don't count after 2 strikes)
    # Foul tip tests
    ("T", "01"),  # 1 foul tip = 1 strike
    ("BT", "11"),  # 1 ball, 1 foul tip = 1 ball, 1 strike
    ("SST", "03"),  # 2 strikes, 1 foul tip = 3 strikes (strikeout)
    ("BBT", "21"),  # 2 balls, 1 foul tip = 2 balls, 1 strike
    ("BBST", "22"),  # 2 balls, 1 strike, 1 foul tip = 2 balls, 2 strikes
    ("BBSST", "23"),  # 2 balls, 2 strikes, 1 foul tip = 2 balls, 3 strikes (strikeout)
            ("SSTT", "03"),  # 2 strikes, 2 foul tips = 3 strikes (strikeout, capped at 3)
        ("FFT", "03"),  # 2 fouls, 1 foul tip = 3 strikes (strikeout)
        ("SFT", "03"),  # 1 strike, 1 foul, 1 foul tip = 3 strikes (strikeout)
])
def test_count_calculation(pitches, expected):
    """Test count calculation with various pitch sequences."""
    actual = calculate_count(pitches)
    assert actual == expected, f"Pitches '{pitches}' should result in count '{expected}', got '{actual}'"


def test_specific_case():
    """Test the specific case from the debug script."""
    pitches = "FFFFBBBBBBBB"
    expected = "42"
    actual = calculate_count(pitches)
    assert actual == expected, f"Pitches '{pitches}' should result in count '{expected}', got '{actual}'"
    
    # Verify breakdown
    balls = 0
    strikes = 0
    for pitch in pitches:
        if pitch == 'B':
            balls += 1
        elif pitch in ['S', 'C']:  # Swinging strike, Called strike
            strikes += 1
        elif pitch == 'F':
            if strikes < 2:
                strikes += 1
    
    assert balls == 8, f"Expected 8 balls, got {balls}"
    assert strikes == 2, f"Expected 2 strikes, got {strikes}"
    assert pitches.count('F') == 4, f"Expected 4 foul balls, got {pitches.count('F')}"
    assert pitches.count('S') + pitches.count('C') == 0, "Expected 0 regular strikes"


def test_foul_tip_strikeout():
    """Test that foul tips on strike 2 result in a strikeout."""
    # Test foul tip on strike 2
    pitches = "SST"  # 2 strikes, then foul tip
    expected = "03"  # 0 balls, 3 strikes (strikeout)
    actual = calculate_count(pitches)
    assert actual == expected, f"Foul tip on strike 2 should result in strikeout: '{pitches}' -> '{expected}', got '{actual}'"
    
    # Test foul tip on strike 1
    pitches = "ST"  # 1 strike, then foul tip
    expected = "02"  # 0 balls, 2 strikes
    actual = calculate_count(pitches)
    assert actual == expected, f"Foul tip on strike 1 should result in 2 strikes: '{pitches}' -> '{expected}', got '{actual}'"
    
    # Test foul tip on 0 strikes
    pitches = "T"  # Foul tip on 0 strikes
    expected = "01"  # 0 balls, 1 strike
    actual = calculate_count(pitches)
    assert actual == expected, f"Foul tip on 0 strikes should result in 1 strike: '{pitches}' -> '{expected}', got '{actual}'" 