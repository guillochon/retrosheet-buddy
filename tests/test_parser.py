"""Tests for the Retrosheet parser."""

import tempfile
from pathlib import Path

import pytest

from retrosheet_buddy.models import EventFile, Game, Play, Player
from retrosheet_buddy.parser import parse_event_file


def test_parse_simple_game():
    """Test parsing a simple game with basic records."""
    event_data = """id,ATL198304080
version,1
info,visteam,"PHI"
info,hometeam,"ATL"
info,date,"1983/04/08"
start,schmi001,"Mike Schmidt",0,1,5
start,murpd001,"Dale Murphy",1,1,8
play,1,0,schmi001,00,,K
play,1,1,murpd001,00,,S8"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.EVN', delete=False) as f:
        f.write(event_data)
        temp_path = Path(f.name)
    
    try:
        event_file = parse_event_file(temp_path)
        
        assert len(event_file.games) == 1
        game = event_file.games[0]
        
        assert game.game_id == "ATL198304080"
        assert game.info.away_team == "PHI"
        assert game.info.home_team == "ATL"
        assert game.info.date == "1983/04/08"
        
        assert len(game.players) == 2
        assert game.players[0].name == "Mike Schmidt"
        assert game.players[1].name == "Dale Murphy"
        
        assert len(game.plays) == 2
        assert game.plays[0].batter_id == "schmi001"
        assert game.plays[0].play_description == "K"
        assert game.plays[1].batter_id == "murpd001"
        assert game.plays[1].play_description == "S8"
        
    finally:
        temp_path.unlink()


def test_parse_empty_file():
    """Test parsing an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.EVN', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        event_file = parse_event_file(temp_path)
        assert len(event_file.games) == 0
    finally:
        temp_path.unlink()


def test_parse_multiple_games():
    """Test parsing multiple games in one file."""
    event_data = """id,ATL198304080
version,1
info,visteam,"PHI"
info,hometeam,"ATL"
play,1,0,schmi001,00,,K
id,ATL198304081
version,1
info,visteam,"NYM"
info,hometeam,"ATL"
play,1,0,strawd001,00,,HR"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.EVN', delete=False) as f:
        f.write(event_data)
        temp_path = Path(f.name)
    
    try:
        event_file = parse_event_file(temp_path)
        
        assert len(event_file.games) == 2
        assert event_file.games[0].game_id == "ATL198304080"
        assert event_file.games[1].game_id == "ATL198304081"
        
    finally:
        temp_path.unlink() 