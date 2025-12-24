"""
Pipeline Settings Service - Manages editable prompts and toggles for the agent pipeline.

Handles storage and retrieval of:
- LIMB test prompts
- Evaluation criteria
- Codebase exploration prompt
- Agent OS blueprint prompt
- Phase breakdown prompt
- Pipeline toggles (pause after stages)
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.models import PipelineSettings, PIPELINE_SETTING_KEYS


# =============================================================================
# DEFAULT PROMPTS
# =============================================================================

DEFAULT_CODEBASE_EXPLORATION_PROMPT = """## Codebase Exploration Request

**Explore this entire codebase and give me a comprehensive summary. I want you to understand:**

- **The overall architecture and how files/folders are organized**
- **The main entry points and how data flows through the app**
- **Key components, their purposes, and how they connect**
- **Any patterns, conventions, or important config files**

**Take your time. Read the important files. When you're done, summarize what this project does and how it works so I can verify you understand it before I ask you to make changes.**"""

DEFAULT_AGENT_OS_BLUEPRINT_PROMPT = """Based on our conversation and the ideas we've discussed, create a comprehensive Agent OS blueprint.

The blueprint should include:
1. **Overview** - What we're building and why
2. **Requirements** - Functional and technical requirements
3. **User Stories** - Key user interactions and flows
4. **Technical Specification** - Architecture, technologies, data models
5. **Success Metrics** - How we'll measure success
6. **Open Questions** - Any remaining uncertainties

Format this as a structured document that can guide implementation."""

DEFAULT_PHASE_BREAKDOWN_PROMPT = """Now take this Agent OS blueprint and break it down into implementation phases.

Each phase should:
1. Be independently testable
2. Build incrementally on previous phases
3. Be small enough to verify correctness before moving on
4. Have clear acceptance criteria

The goal is to create small, testable chunks that minimize errors. We'll build Phase 1, test it, then Phase 2, test it, and so on until we have a complete, working system.

Format as:
- Phase 1: [Description] - [Test criteria]
- Phase 2: [Description] - [Test criteria]
- etc.

After all phases, we'll do a final integration test of the complete system."""

DEFAULT_PHASE_TEST_PROMPT = """Test the code from Phase {phase_number}.

Verify:
1. All acceptance criteria from the phase are met
2. No regressions from previous phases
3. Code runs without errors
4. Edge cases are handled

Report any issues found. If all tests pass, confirm ready for next phase."""

DEFAULT_INTEGRATION_TEST_PROMPT = """Run final integration tests on the complete system.

Verify:
1. All phases work together correctly
2. End-to-end user flows function as expected
3. No integration issues between components
4. Performance is acceptable
5. Error handling works correctly

Report the test results and overall system readiness."""


# =============================================================================
# SERVICE FUNCTIONS
# =============================================================================

def get_pipeline_setting(
    db: Session,
    user_id: int,
    setting_key: str,
    project_id: Optional[int] = None
) -> Optional[str]:
    """
    Get a pipeline setting value.

    Checks project-specific first, then falls back to user default.

    Args:
        db: Database session
        user_id: User ID
        setting_key: Setting key from PIPELINE_SETTING_KEYS
        project_id: Optional project ID for project-specific settings

    Returns:
        Setting value or None
    """
    # Try project-specific first
    if project_id:
        setting = db.query(PipelineSettings).filter(
            and_(
                PipelineSettings.user_id == user_id,
                PipelineSettings.project_id == project_id,
                PipelineSettings.setting_key == setting_key
            )
        ).first()
        if setting:
            return setting.setting_value

    # Fall back to user default (no project)
    setting = db.query(PipelineSettings).filter(
        and_(
            PipelineSettings.user_id == user_id,
            PipelineSettings.project_id == None,
            PipelineSettings.setting_key == setting_key
        )
    ).first()

    return setting.setting_value if setting else None


def set_pipeline_setting(
    db: Session,
    user_id: int,
    setting_key: str,
    setting_value: str,
    project_id: Optional[int] = None
) -> PipelineSettings:
    """
    Set a pipeline setting value.

    Args:
        db: Database session
        user_id: User ID
        setting_key: Setting key
        setting_value: Setting value
        project_id: Optional project ID for project-specific settings

    Returns:
        The PipelineSettings record
    """
    # Check if exists
    query = db.query(PipelineSettings).filter(
        and_(
            PipelineSettings.user_id == user_id,
            PipelineSettings.setting_key == setting_key
        )
    )

    if project_id:
        query = query.filter(PipelineSettings.project_id == project_id)
    else:
        query = query.filter(PipelineSettings.project_id == None)

    setting = query.first()

    if setting:
        setting.setting_value = setting_value
        setting.updated_at = datetime.utcnow()
    else:
        setting = PipelineSettings(
            user_id=user_id,
            project_id=project_id,
            setting_key=setting_key,
            setting_value=setting_value
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting


def get_all_pipeline_settings(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None
) -> Dict[str, str]:
    """
    Get all pipeline settings for a user/project.

    Args:
        db: Database session
        user_id: User ID
        project_id: Optional project ID

    Returns:
        Dict of setting_key -> setting_value
    """
    settings = {}

    # Get user defaults first
    user_settings = db.query(PipelineSettings).filter(
        and_(
            PipelineSettings.user_id == user_id,
            PipelineSettings.project_id == None
        )
    ).all()

    for s in user_settings:
        settings[s.setting_key] = s.setting_value

    # Override with project-specific if provided
    if project_id:
        project_settings = db.query(PipelineSettings).filter(
            and_(
                PipelineSettings.user_id == user_id,
                PipelineSettings.project_id == project_id
            )
        ).all()

        for s in project_settings:
            settings[s.setting_key] = s.setting_value

    return settings


def get_pipeline_setting_with_default(
    db: Session,
    user_id: int,
    setting_key: str,
    project_id: Optional[int] = None
) -> str:
    """
    Get a pipeline setting with fallback to default.

    Args:
        db: Database session
        user_id: User ID
        setting_key: Setting key
        project_id: Optional project ID

    Returns:
        Setting value or default
    """
    value = get_pipeline_setting(db, user_id, setting_key, project_id)

    if value is not None:
        return value

    # Return defaults
    defaults = {
        "codebase_exploration_prompt": DEFAULT_CODEBASE_EXPLORATION_PROMPT,
        "agent_os_blueprint_prompt": DEFAULT_AGENT_OS_BLUEPRINT_PROMPT,
        "phase_breakdown_prompt": DEFAULT_PHASE_BREAKDOWN_PROMPT,
        "phase_test_prompt": DEFAULT_PHASE_TEST_PROMPT,
        "integration_test_prompt": DEFAULT_INTEGRATION_TEST_PROMPT,
        "pause_after_agent_os": "false",
        "pause_after_phases": "false",
        "pause_before_build": "false",
        "auto_retry_on_fail": "true",
        "max_retry_attempts": "3",
    }

    return defaults.get(setting_key, "")


def get_toggle(
    db: Session,
    user_id: int,
    toggle_key: str,
    project_id: Optional[int] = None
) -> bool:
    """
    Get a boolean toggle setting.

    Args:
        db: Database session
        user_id: User ID
        toggle_key: Toggle key (e.g., "pause_after_agent_os")
        project_id: Optional project ID

    Returns:
        Boolean value
    """
    value = get_pipeline_setting_with_default(db, user_id, toggle_key, project_id)
    return value.lower() in ("true", "1", "yes", "on")


def set_toggle(
    db: Session,
    user_id: int,
    toggle_key: str,
    value: bool,
    project_id: Optional[int] = None
) -> PipelineSettings:
    """
    Set a boolean toggle setting.

    Args:
        db: Database session
        user_id: User ID
        toggle_key: Toggle key
        value: Boolean value
        project_id: Optional project ID

    Returns:
        The PipelineSettings record
    """
    return set_pipeline_setting(
        db, user_id, toggle_key,
        "true" if value else "false",
        project_id
    )


def initialize_default_settings(db: Session, user_id: int) -> None:
    """
    Initialize default pipeline settings for a user.

    Args:
        db: Database session
        user_id: User ID
    """
    defaults = {
        "codebase_exploration_prompt": DEFAULT_CODEBASE_EXPLORATION_PROMPT,
        "agent_os_blueprint_prompt": DEFAULT_AGENT_OS_BLUEPRINT_PROMPT,
        "phase_breakdown_prompt": DEFAULT_PHASE_BREAKDOWN_PROMPT,
        "phase_test_prompt": DEFAULT_PHASE_TEST_PROMPT,
        "integration_test_prompt": DEFAULT_INTEGRATION_TEST_PROMPT,
        "pause_after_agent_os": "false",
        "pause_after_phases": "false",
        "pause_before_build": "false",
        "auto_retry_on_fail": "true",
        "max_retry_attempts": "3",
    }

    for key, value in defaults.items():
        # Only set if not already set
        if not get_pipeline_setting(db, user_id, key):
            set_pipeline_setting(db, user_id, key, value)
