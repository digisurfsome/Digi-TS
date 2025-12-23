"""
Settings management service.

Handles application and user settings.
"""

from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.models import Settings


# Available AI models for dropdowns (updated Dec 2025)
OPENAI_MODELS = [
    # GPT-5 Series (Latest)
    "gpt-5.2",
    "gpt-5.1",
    # GPT-4.1 Series
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    # GPT-4o Series
    "gpt-4o",
    "gpt-4o-mini",
    # Reasoning Models
    "o4-mini",
    "o1",
    "o1-mini",
    # Legacy (still available)
    "gpt-4-turbo-preview",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

ANTHROPIC_MODELS = [
    # Claude 4.5 Series (Latest)
    "claude-opus-4-5-20251101",
    "claude-sonnet-4-5-20250929",
    # Claude 4 Series
    "claude-opus-4-1-20250805",
    "claude-sonnet-4-20250514",
    # Claude 3.5 (Legacy but still good)
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    # Aliases (auto-update to latest)
    "claude-sonnet-4",
    "claude-opus-4",
]

GEMINI_MODELS = [
    # Gemini 3 Series (Latest)
    "gemini-3-pro",
    "gemini-3-deep-think",
    # Gemini 2.5 Series
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    # Gemini 2.0 Series
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    # Legacy
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

# All models combined for general selection
ALL_CHAT_MODELS = OPENAI_MODELS + ANTHROPIC_MODELS + GEMINI_MODELS

# Default setting values
DEFAULT_SETTINGS = {
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
    "GOOGLE_API_KEY": "",
    "DEFAULT_CHAT_MODEL": "gpt-4.1",
    "DEFAULT_SUMMARY_MODEL": "gpt-4.1-mini",
    "max_context_tokens": "128000",
    "auto_baton_threshold_percent": "80",
    "auto_warmup_enabled": "true",
    "warmup_prompt_1": "Review the project context and understand the design system.",
    "warmup_prompt_2": "Analyze the current node structure and relationships.",
    "warmup_prompt_3": "Consider the project goals and constraints.",
    "warmup_prompt_4": "Prepare to assist with design decisions and implementation.",
    "baton_description_prompt": "Summarize the current state of the project, including key design decisions, active nodes, and recent changes. Focus on what's important for understanding the project context.",
    "pin_code": "",
}


def get_setting(
    db: Session,
    key: str,
    user_id: Optional[int] = None,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Get a setting value.

    Args:
        db: Database session
        key: Setting key
        user_id: User ID for user-specific settings (None for global)
        default: Default value if setting doesn't exist

    Returns:
        Setting value or default
    """
    query = db.query(Settings).filter(Settings.setting_key == key)

    if user_id is not None:
        query = query.filter(Settings.user_id == user_id)
    else:
        query = query.filter(Settings.is_global == True)

    setting = query.first()

    if setting:
        return setting.setting_value

    # Return default from DEFAULT_SETTINGS or provided default
    if default is not None:
        return default

    return DEFAULT_SETTINGS.get(key)


def set_setting(
    db: Session,
    key: str,
    value: str,
    user_id: Optional[int] = None,
    description: Optional[str] = None
) -> Settings:
    """
    Set a setting value.

    Args:
        db: Database session
        key: Setting key
        value: Setting value
        user_id: User ID for user-specific settings (None for global)
        description: Optional description

    Returns:
        Created or updated Settings
    """
    query = db.query(Settings).filter(Settings.setting_key == key)

    if user_id is not None:
        query = query.filter(Settings.user_id == user_id)
    else:
        query = query.filter(Settings.is_global == True)

    setting = query.first()

    if setting:
        # Update existing
        setting.setting_value = value
        if description is not None:
            setting.description = description
        db.commit()
        db.refresh(setting)
    else:
        # Create new
        setting = Settings(
            setting_key=key,
            setting_value=value,
            user_id=user_id,
            is_global=(user_id is None),
            description=description
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return setting


def get_all_settings(
    db: Session,
    user_id: Optional[int] = None
) -> Dict[str, str]:
    """
    Get all settings as a dictionary.

    Args:
        db: Database session
        user_id: User ID for user-specific settings (None for global)

    Returns:
        Dictionary of setting key-value pairs
    """
    query = db.query(Settings)

    if user_id is not None:
        query = query.filter(Settings.user_id == user_id)
    else:
        query = query.filter(Settings.is_global == True)

    settings = query.all()

    # Start with defaults
    result = dict(DEFAULT_SETTINGS)

    # Override with database values
    for setting in settings:
        result[setting.setting_key] = setting.setting_value or ""

    return result


def set_multiple_settings(
    db: Session,
    settings_dict: Dict[str, str],
    user_id: Optional[int] = None
) -> None:
    """
    Set multiple settings at once.

    Args:
        db: Database session
        settings_dict: Dictionary of setting key-value pairs
        user_id: User ID for user-specific settings (None for global)
    """
    for key, value in settings_dict.items():
        set_setting(db, key, value, user_id)


def delete_setting(
    db: Session,
    key: str,
    user_id: Optional[int] = None
) -> bool:
    """
    Delete a setting.

    Args:
        db: Database session
        key: Setting key
        user_id: User ID for user-specific settings (None for global)

    Returns:
        True if deleted, False if not found
    """
    query = db.query(Settings).filter(Settings.setting_key == key)

    if user_id is not None:
        query = query.filter(Settings.user_id == user_id)
    else:
        query = query.filter(Settings.is_global == True)

    setting = query.first()

    if setting:
        db.delete(setting)
        db.commit()
        return True

    return False


def get_setting_as_int(
    db: Session,
    key: str,
    user_id: Optional[int] = None,
    default: int = 0
) -> int:
    """
    Get a setting as an integer.

    Args:
        db: Database session
        key: Setting key
        user_id: User ID for user-specific settings
        default: Default value

    Returns:
        Setting value as integer
    """
    value = get_setting(db, key, user_id)
    if value is None:
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_setting_as_bool(
    db: Session,
    key: str,
    user_id: Optional[int] = None,
    default: bool = False
) -> bool:
    """
    Get a setting as a boolean.

    Args:
        db: Database session
        key: Setting key
        user_id: User ID for user-specific settings
        default: Default value

    Returns:
        Setting value as boolean
    """
    value = get_setting(db, key, user_id)
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")
