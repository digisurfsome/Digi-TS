"""
Settings management service.

Handles application and user settings.
"""

from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.models import Settings


# Default setting values
DEFAULT_SETTINGS = {
    "OPENAI_API_KEY": "",
    "DEFAULT_CHAT_MODEL": "gpt-4-turbo-preview",
    "DEFAULT_SUMMARY_MODEL": "gpt-4-turbo-preview",
    "max_context_tokens": "8000",
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
