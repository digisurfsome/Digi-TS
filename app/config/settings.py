"""
Configuration settings for Design Tree Studio.

Loads environment variables and provides application-wide configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        ""
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "Design Tree Studio")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate that required settings are configured.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is not configured")

        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not configured")

        return len(errors) == 0, errors

    @classmethod
    def get_db_url(cls) -> str:
        """Get the database URL, with helpful error message if not set."""
        if not cls.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL not configured. "
                "Please set it in your .env file or environment variables."
            )
        return cls.DATABASE_URL


# Create a singleton instance
settings = Settings()
