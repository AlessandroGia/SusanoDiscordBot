from unittest.mock import MagicMock
from src.voice.voice_state.voice_player import VoicePlayer

def test_get_player():
    mock_player = MagicMock()
    voice_player = VoicePlayer(mock_player)
    assert voice_player.get_player() == mock_player

def test_ensure_guild_state():
    guild_state