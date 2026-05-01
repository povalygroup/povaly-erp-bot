"""Setup configuration for Telegram Operations Automation System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telegram-ops-automation",
    version="1.0.0",
    author="Povaly Group",
    description="Enterprise-grade Telegram bot for task workflow management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/povaly/telegram-ops-automation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "python-telegram-bot>=20.7",
        "python-dotenv>=1.0.0",
        "APScheduler>=3.10.4",
        "pytz>=2023.3",
        "aiosqlite>=0.19.0",
        "motor>=3.3.2",
        "aiofiles>=23.2.1",
        "cryptography>=41.0.7",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "hypothesis>=6.92.1",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "isort>=5.13.2",
            "ipython>=8.18.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "telegram-ops-bot=src.main:main",
        ],
    },
)
