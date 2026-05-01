"""Bot handlers."""

from .command_handler import setup_command_handlers
from .message_handler import setup_message_handlers
from .reaction_handler import setup_reaction_handlers

__all__ = [
    'setup_command_handlers',
    'setup_message_handlers',
    'setup_reaction_handlers',
]
