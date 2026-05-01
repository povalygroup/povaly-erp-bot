"""
Script to generate the complete project structure with placeholder implementations.
This creates all necessary files with basic structure to enable development.
"""

import os
from pathlib import Path


def create_file(path: str, content: str):
    """Create a file with given content."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")


def generate_structure():
    """Generate the complete project structure."""
    
    # Utility files
    files = {
        "src/utils/format_utils.py": '''"""Message formatting utilities."""

def format_user_mention(user_id: int, username: str) -> str:
    """Format user mention."""
    return f"@{username}" if username else f"User {user_id}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_ticket_list(tickets: list, with_links: bool = False) -> str:
    """Format list of tickets."""
    if not tickets:
        return "No tickets"
    return "\\n".join(f"• {ticket}" for ticket in tickets)
''',

        "src/utils/link_builder.py": '''"""Telegram message link builder."""

def build_message_link(group_id: int, message_id: int) -> str:
    """
    Build Telegram message link.
    
    Args:
        group_id: Telegram group ID (negative number)
        message_id: Message ID
    
    Returns:
        Clickable message link
    """
    # Remove the -100 prefix from group ID for link
    clean_group_id = str(abs(group_id))[3:] if str(abs(group_id)).startswith("100") else str(abs(group_id))
    return f"https://t.me/c/{clean_group_id}/{message_id}"
''',

        "src/utils/validators.py": '''"""Input validation functions."""

import re
from typing import Optional


def validate_ticket_format(ticket: str, pattern: str) -> bool:
    """Validate ticket format against regex pattern."""
    return bool(re.match(pattern, ticket))


def validate_brand_code(brand: str, valid_brands: list) -> bool:
    """Validate brand code."""
    return brand in valid_brands


def extract_username(text: str) -> Optional[str]:
    """Extract @username from text."""
    match = re.search(r'@(\\w+)', text)
    return match.group(1) if match else None


def extract_all_usernames(text: str) -> list:
    """Extract all @usernames from text."""
    return re.findall(r'@(\\w+)', text)
''',

        "src/bot/__init__.py": '''"""Bot application layer."""''',

        "src/bot/application.py": '''"""Bot application setup."""

import logging
from telegram.ext import Application

from src.config import Config
from src.bot.handlers.message_handler import setup_message_handlers
from src.bot.handlers.reaction_handler import setup_reaction_handlers

logger = logging.getLogger(__name__)


async def setup_bot_application(config: Config) -> Application:
    """
    Setup and configure the bot application.
    
    Args:
        config: System configuration
    
    Returns:
        Configured Application instance
    """
    logger.info("Building bot application...")
    
    # Create application
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Setup handlers
    setup_message_handlers(application, config)
    setup_reaction_handlers(application, config)
    
    logger.info("Bot application built successfully")
    return application
''',

        "src/bot/handlers/__init__.py": '''"""Bot handlers."""''',

        "src/bot/handlers/message_handler.py": '''"""Message handler."""

import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from src.config import Config

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    if not update.message or not update.message.text:
        return
    
    logger.info(
        f"Received message from user {update.message.from_user.id}: {update.message.text[:50]}"
    )
    
    # TODO: Implement message routing and processing


def setup_message_handlers(application: Application, config: Config):
    """Setup message handlers."""
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    logger.info("Message handlers registered")
''',

        "src/bot/handlers/reaction_handler.py": '''"""Reaction handler."""

import logging
from telegram import Update
from telegram.ext import Application, MessageReactionHandler, ContextTypes

from src.config import Config

logger = logging.getLogger(__name__)


async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle message reactions."""
    if not update.message_reaction:
        return
    
    logger.info(
        f"Received reaction from user {update.message_reaction.user.id}"
    )
    
    # TODO: Implement reaction processing


def setup_reaction_handlers(application: Application, config: Config):
    """Setup reaction handlers."""
    application.add_handler(MessageReactionHandler(handle_reaction))
    logger.info("Reaction handlers registered")
''',

        "src/core/__init__.py": '''"""Core business logic layer."""''',

        "src/core/parser/__init__.py": '''"""Message parsers."""''',

        "src/core/parser/message_parser.py": '''"""Message parsing logic."""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ParsedTask:
    """Parsed task data."""
    ticket: str
    assignee: Optional[str]
    description: str


@dataclass
class ParsedQASubmission:
    """Parsed QA submission data."""
    ticket: str
    brand: str
    asset: str


@dataclass
class ParsedRejectFeedback:
    """Parsed reject feedback data."""
    ticket: str
    issue_type: str
    problem: str
    fix_required: str
    assignee: str


class MessageParser:
    """Message parser for structured formats."""
    
    def parse_task(self, text: str) -> Optional[ParsedTask]:
        """Parse task message."""
        # TODO: Implement task parsing
        return None
    
    def parse_qa_submission(self, text: str) -> Optional[ParsedQASubmission]:
        """Parse QA submission message."""
        # Pattern: [TICKET][BRAND][ASSET]
        pattern = r'\\[([^\\]]+)\\]\\[([^\\]]+)\\]\\[([^\\]]+)\\]'
        match = re.search(pattern, text)
        
        if match:
            return ParsedQASubmission(
                ticket=match.group(1).strip(),
                brand=match.group(2).strip(),
                asset=match.group(3).strip()
            )
        return None
    
    def parse_reject_feedback(self, text: str) -> Optional[ParsedRejectFeedback]:
        """Parse reject feedback message."""
        # Pattern: [TICKET][ISSUE_TYPE][PROBLEM][FIX_REQUIRED][ASSIGNEE]
        pattern = r'\\[([^\\]]+)\\]\\[([^\\]]+)\\]\\[([^\\]]+)\\]\\[([^\\]]+)\\]\\[([^\\]]+)\\]'
        match = re.search(pattern, text)
        
        if match:
            return ParsedRejectFeedback(
                ticket=match.group(1).strip(),
                issue_type=match.group(2).strip(),
                problem=match.group(3).strip(),
                fix_required=match.group(4).strip(),
                assignee=match.group(5).strip()
            )
        return None
''',

        "src/services/__init__.py": '''"""Service layer."""''',

        "src/security/__init__.py": '''"""Security layer."""''',

        "pytest.ini": '''[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
''',

        "tests/__init__.py": '''"""Test suite."""''',

        "tests/conftest.py": '''"""Pytest configuration and fixtures."""

import pytest
from src.config import Config


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        TELEGRAM_BOT_TOKEN="test_token",
        TELEGRAM_GROUP_ID=-1001234567890,
        DATABASE_TYPE="sqlite",
        DATABASE_PATH=":memory:",
        DATABASE_ENCRYPTION_KEY="test_key_32_characters_long!!!",
        BRAND_CODES=["PV", "VB"],
        ADMINISTRATORS=[123456789],
    )
''',

        ".dockerignore": '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# Environment variables
.env

# Database
*.db
*.sqlite
*.sqlite3
data/
backups/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Git
.git/
.gitignore

# Documentation
docs/
*.md

# Tests
tests/
''',

        "Makefile": '''# Makefile for Telegram Operations Automation System

.PHONY: help install dev-install test lint format clean run docker-build docker-up docker-down

help:
\t@echo "Available commands:"
\t@echo "  install      - Install production dependencies"
\t@echo "  dev-install  - Install development dependencies"
\t@echo "  test         - Run tests"
\t@echo "  lint         - Run linters"
\t@echo "  format       - Format code"
\t@echo "  clean        - Clean build artifacts"
\t@echo "  run          - Run the bot"
\t@echo "  docker-build - Build Docker image"
\t@echo "  docker-up    - Start Docker containers"
\t@echo "  docker-down  - Stop Docker containers"

install:
\tpip install -r requirements.txt

dev-install:
\tpip install -r requirements.txt
\tpip install -e ".[dev]"

test:
\tpytest

lint:
\tflake8 src tests
\tmypy src

format:
\tblack src tests
\tisort src tests

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {} +
\tfind . -type f -name "*.pyc" -delete
\tfind . -type f -name "*.pyo" -delete
\tfind . -type d -name "*.egg-info" -exec rm -rf {} +
\trm -rf build dist .pytest_cache .coverage htmlcov

run:
\tpython -m src.main

docker-build:
\tdocker-compose build

docker-up:
\tdocker-compose up -d

docker-down:
\tdocker-compose down
''',
    }
    
    # Create all files
    for path, content in files.items():
        create_file(path, content)
    
    print("\\n✅ Project structure generated successfully!")
    print("\\n📝 Next steps:")
    print("1. Review generated files")
    print("2. Implement TODO items in each file")
    print("3. Run tests: pytest")
    print("4. Start development!")


if __name__ == "__main__":
    generate_structure()
