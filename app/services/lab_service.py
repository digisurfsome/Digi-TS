"""
Lab Service - Configuration and Test Management for Agent OS.

Provides Lab Mode functionality including:
- Feature flag management
- Test configuration saving/loading
- Test metrics tracking
- A/B testing support
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json

from sqlalchemy.orm import Session as DBSession

from app.services.process_log import ProcessLog


# ============================================================================
# FEATURE FLAGS
# ============================================================================


class FeatureFlag(str, Enum):
    """Available feature flags for Lab Mode."""
    REAL_TIME_TAGGING = "real_time_tagging"
    CLICK_TO_RANT = "click_to_rant"
    FLASH_LABELS = "flash_labels"
    GAP_DETECTION = "gap_detection"
    TAG_OVERLAY = "tag_overlay"
    MULTI_PANEL_VIEW = "multi_panel_view"
    COCKPIT_MODE = "cockpit_mode"
    AUTO_CONSOLIDATE = "auto_consolidate"
    POST_RANT_ANALYSIS = "post_rant_analysis"


# Default feature states
DEFAULT_FEATURE_FLAGS = {
    FeatureFlag.REAL_TIME_TAGGING: True,
    FeatureFlag.CLICK_TO_RANT: True,
    FeatureFlag.FLASH_LABELS: True,
    FeatureFlag.GAP_DETECTION: True,
    FeatureFlag.TAG_OVERLAY: True,
    FeatureFlag.MULTI_PANEL_VIEW: True,
    FeatureFlag.COCKPIT_MODE: False,  # Off by default
    FeatureFlag.AUTO_CONSOLIDATE: False,
    FeatureFlag.POST_RANT_ANALYSIS: True,
}


# ============================================================================
# CONFIGURATION SETTINGS
# ============================================================================


class DetectionSensitivity(str, Enum):
    """Sensitivity levels for auto-detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FlashLabelTiming(str, Enum):
    """When to show flash labels."""
    IMMEDIATE = "immediate"
    AFTER_5S = "after_5s"
    MANUAL = "manual"


class PanelLayout(str, Enum):
    """Panel layout modes."""
    STANDARD = "standard"
    COCKPIT = "cockpit"


class ColorTheme(str, Enum):
    """UI color themes."""
    DEFAULT = "default"
    HIGH_CONTRAST = "high_contrast"


class AnimationSpeed(str, Enum):
    """Animation speed settings."""
    OFF = "off"
    FAST = "fast"
    NORMAL = "normal"


class RequiredSections(str, Enum):
    """Required sections level."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPLETE = "complete"


@dataclass
class ConfigSettings:
    """Complete configuration settings for Agent OS Lab Mode."""
    # General
    auto_detect_nodes: bool = True
    detection_sensitivity: DetectionSensitivity = DetectionSensitivity.MEDIUM
    flash_label_timing: FlashLabelTiming = FlashLabelTiming.IMMEDIATE

    # Voice
    transcription_model: str = "whisper-1"
    voice_timeout: int = 30  # seconds (5, 10, 30, or continuous)

    # Display
    panel_layout: PanelLayout = PanelLayout.STANDARD
    color_theme: ColorTheme = ColorTheme.DEFAULT
    animation_speed: AnimationSpeed = AnimationSpeed.NORMAL

    # Agent OS
    required_sections: RequiredSections = RequiredSections.STANDARD
    gap_threshold: int = 70  # percentage (50, 70, 90)
    auto_consolidate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "auto_detect_nodes": self.auto_detect_nodes,
            "detection_sensitivity": self.detection_sensitivity.value,
            "flash_label_timing": self.flash_label_timing.value,
            "transcription_model": self.transcription_model,
            "voice_timeout": self.voice_timeout,
            "panel_layout": self.panel_layout.value,
            "color_theme": self.color_theme.value,
            "animation_speed": self.animation_speed.value,
            "required_sections": self.required_sections.value,
            "gap_threshold": self.gap_threshold,
            "auto_consolidate": self.auto_consolidate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSettings":
        """Create from dictionary."""
        return cls(
            auto_detect_nodes=data.get("auto_detect_nodes", True),
            detection_sensitivity=DetectionSensitivity(
                data.get("detection_sensitivity", "medium")
            ),
            flash_label_timing=FlashLabelTiming(
                data.get("flash_label_timing", "immediate")
            ),
            transcription_model=data.get("transcription_model", "whisper-1"),
            voice_timeout=data.get("voice_timeout", 30),
            panel_layout=PanelLayout(
                data.get("panel_layout", "standard")
            ),
            color_theme=ColorTheme(
                data.get("color_theme", "default")
            ),
            animation_speed=AnimationSpeed(
                data.get("animation_speed", "normal")
            ),
            required_sections=RequiredSections(
                data.get("required_sections", "standard")
            ),
            gap_threshold=data.get("gap_threshold", 70),
            auto_consolidate=data.get("auto_consolidate", False),
        )


# Default configuration
DEFAULT_CONFIG = ConfigSettings()


# ============================================================================
# TEST CONFIGURATION
# ============================================================================


@dataclass
class TestConfiguration:
    """A saved test configuration for Lab Mode."""
    id: str
    name: str
    description: str
    feature_flags: Dict[str, bool]
    config_settings: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "feature_flags": self.feature_flags,
            "config_settings": self.config_settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestConfiguration":
        """Create from dictionary."""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            feature_flags=data.get("feature_flags", {}),
            config_settings=data.get("config_settings", {}),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
        )


# ============================================================================
# TEST METRICS
# ============================================================================


@dataclass
class TestMetrics:
    """Metrics tracked during a test session."""
    config_id: str
    session_start: datetime
    session_end: Optional[datetime] = None

    # Usage metrics
    total_rants: int = 0
    total_words: int = 0
    total_duration_seconds: float = 0.0

    # Completion metrics
    completion_start: int = 0  # % at start
    completion_end: int = 0    # % at end
    sections_filled: int = 0
    gaps_closed: int = 0

    # Feature usage
    features_used: Dict[str, int] = field(default_factory=dict)

    # User feedback
    notes: str = ""
    rating: Optional[int] = None  # 1-5 stars

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "config_id": self.config_id,
            "session_start": self.session_start.isoformat(),
            "session_end": self.session_end.isoformat() if self.session_end else None,
            "total_rants": self.total_rants,
            "total_words": self.total_words,
            "total_duration_seconds": self.total_duration_seconds,
            "completion_start": self.completion_start,
            "completion_end": self.completion_end,
            "sections_filled": self.sections_filled,
            "gaps_closed": self.gaps_closed,
            "features_used": self.features_used,
            "notes": self.notes,
            "rating": self.rating,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestMetrics":
        """Create from dictionary."""
        session_start = data.get("session_start")
        session_end = data.get("session_end")

        if isinstance(session_start, str):
            session_start = datetime.fromisoformat(session_start)
        if isinstance(session_end, str) and session_end:
            session_end = datetime.fromisoformat(session_end)

        return cls(
            config_id=data.get("config_id", ""),
            session_start=session_start or datetime.utcnow(),
            session_end=session_end,
            total_rants=data.get("total_rants", 0),
            total_words=data.get("total_words", 0),
            total_duration_seconds=data.get("total_duration_seconds", 0.0),
            completion_start=data.get("completion_start", 0),
            completion_end=data.get("completion_end", 0),
            sections_filled=data.get("sections_filled", 0),
            gaps_closed=data.get("gaps_closed", 0),
            features_used=data.get("features_used", {}),
            notes=data.get("notes", ""),
            rating=data.get("rating"),
        )


# ============================================================================
# LAB SERVICE CLASS
# ============================================================================


class LabService:
    """
    Lab Service for managing test configurations and metrics.

    Provides:
    - Feature flag management
    - Configuration saving/loading
    - Test metrics tracking
    - Session management for Lab Mode
    """

    def __init__(self):
        """Initialize the lab service."""
        self._feature_flags: Dict[str, bool] = {
            f.value: v for f, v in DEFAULT_FEATURE_FLAGS.items()
        }
        self._config: ConfigSettings = DEFAULT_CONFIG
        self._configurations: Dict[str, TestConfiguration] = {}
        self._metrics_history: List[TestMetrics] = []
        self._current_test: Optional[TestMetrics] = None
        self._lab_mode_active: bool = False

    # =========================================================================
    # FEATURE FLAG MANAGEMENT
    # =========================================================================

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return self._feature_flags.copy()

    def is_feature_enabled(self, feature: FeatureFlag) -> bool:
        """Check if a feature is enabled."""
        return self._feature_flags.get(feature.value, False)

    def set_feature_flag(self, feature: FeatureFlag, enabled: bool) -> None:
        """Set a feature flag."""
        self._feature_flags[feature.value] = enabled
        ProcessLog.info(
            "LabService",
            f"Feature {feature.value} set to {enabled}"
        )

    def set_all_feature_flags(self, flags: Dict[str, bool]) -> None:
        """Set multiple feature flags at once."""
        for key, value in flags.items():
            if key in [f.value for f in FeatureFlag]:
                self._feature_flags[key] = value

    def reset_feature_flags(self) -> None:
        """Reset all feature flags to defaults."""
        self._feature_flags = {
            f.value: v for f, v in DEFAULT_FEATURE_FLAGS.items()
        }
        ProcessLog.info("LabService", "Feature flags reset to defaults")

    # =========================================================================
    # CONFIGURATION MANAGEMENT
    # =========================================================================

    def get_config(self) -> ConfigSettings:
        """Get current configuration settings."""
        return self._config

    def set_config(self, config: ConfigSettings) -> None:
        """Set configuration settings."""
        self._config = config
        ProcessLog.info("LabService", "Configuration updated")

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update specific configuration settings."""
        config_dict = self._config.to_dict()
        config_dict.update(updates)
        self._config = ConfigSettings.from_dict(config_dict)

    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        self._config = DEFAULT_CONFIG
        ProcessLog.info("LabService", "Configuration reset to defaults")

    # =========================================================================
    # TEST CONFIGURATION MANAGEMENT
    # =========================================================================

    def create_test_config(
        self,
        name: str,
        description: str = ""
    ) -> TestConfiguration:
        """
        Create a new test configuration from current settings.

        Args:
            name: Configuration name
            description: Optional description

        Returns:
            Created TestConfiguration
        """
        import uuid

        config = TestConfiguration(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            feature_flags=self._feature_flags.copy(),
            config_settings=self._config.to_dict(),
        )

        self._configurations[config.id] = config

        ProcessLog.success(
            "LabService",
            f"Created test configuration: {name}",
            details={"id": config.id}
        )

        return config

    def get_test_config(self, config_id: str) -> Optional[TestConfiguration]:
        """Get a test configuration by ID."""
        return self._configurations.get(config_id)

    def list_test_configs(self) -> List[TestConfiguration]:
        """List all saved test configurations."""
        return list(self._configurations.values())

    def load_test_config(self, config_id: str) -> bool:
        """
        Load a test configuration as the active configuration.

        Args:
            config_id: Configuration ID to load

        Returns:
            True if loaded successfully
        """
        config = self._configurations.get(config_id)
        if not config:
            ProcessLog.warning("LabService", f"Configuration not found: {config_id}")
            return False

        # Apply feature flags
        self._feature_flags = config.feature_flags.copy()

        # Apply config settings
        self._config = ConfigSettings.from_dict(config.config_settings)

        ProcessLog.success(
            "LabService",
            f"Loaded test configuration: {config.name}"
        )

        return True

    def delete_test_config(self, config_id: str) -> bool:
        """Delete a test configuration."""
        if config_id in self._configurations:
            name = self._configurations[config_id].name
            del self._configurations[config_id]
            ProcessLog.info("LabService", f"Deleted configuration: {name}")
            return True
        return False

    def update_test_config(
        self,
        config_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[TestConfiguration]:
        """Update a test configuration's metadata."""
        config = self._configurations.get(config_id)
        if not config:
            return None

        if name:
            config.name = name
        if description is not None:
            config.description = description

        config.updated_at = datetime.utcnow()

        # Also update the stored flags and settings
        config.feature_flags = self._feature_flags.copy()
        config.config_settings = self._config.to_dict()

        return config

    # =========================================================================
    # LAB MODE & TEST SESSION MANAGEMENT
    # =========================================================================

    def is_lab_mode_active(self) -> bool:
        """Check if Lab Mode is active."""
        return self._lab_mode_active

    def start_lab_mode(self, config_id: Optional[str] = None) -> bool:
        """
        Start Lab Mode with optional configuration.

        Args:
            config_id: Optional configuration to load

        Returns:
            True if started successfully
        """
        if config_id:
            if not self.load_test_config(config_id):
                return False

        self._lab_mode_active = True
        ProcessLog.info("LabService", "Lab Mode started")
        return True

    def stop_lab_mode(self) -> None:
        """Stop Lab Mode."""
        self._lab_mode_active = False
        ProcessLog.info("LabService", "Lab Mode stopped")

    def start_test_session(
        self,
        config_id: str,
        initial_completion: int = 0
    ) -> TestMetrics:
        """
        Start a new test session.

        Args:
            config_id: Configuration being tested
            initial_completion: Starting completion percentage

        Returns:
            New TestMetrics instance
        """
        self._current_test = TestMetrics(
            config_id=config_id,
            session_start=datetime.utcnow(),
            completion_start=initial_completion,
        )

        ProcessLog.info(
            "LabService",
            f"Test session started for config: {config_id}"
        )

        return self._current_test

    def get_current_test(self) -> Optional[TestMetrics]:
        """Get the current test session metrics."""
        return self._current_test

    def update_test_metrics(
        self,
        rants_added: int = 0,
        words_added: int = 0,
        duration_added: float = 0.0,
        feature_used: Optional[str] = None
    ) -> None:
        """Update metrics for the current test session."""
        if not self._current_test:
            return

        self._current_test.total_rants += rants_added
        self._current_test.total_words += words_added
        self._current_test.total_duration_seconds += duration_added

        if feature_used:
            if feature_used not in self._current_test.features_used:
                self._current_test.features_used[feature_used] = 0
            self._current_test.features_used[feature_used] += 1

    def end_test_session(
        self,
        final_completion: int = 0,
        sections_filled: int = 0,
        gaps_closed: int = 0,
        notes: str = "",
        rating: Optional[int] = None
    ) -> Optional[TestMetrics]:
        """
        End the current test session.

        Args:
            final_completion: Ending completion percentage
            sections_filled: Number of sections filled during test
            gaps_closed: Number of gaps closed during test
            notes: User notes about the test
            rating: Optional 1-5 rating

        Returns:
            Completed TestMetrics
        """
        if not self._current_test:
            return None

        self._current_test.session_end = datetime.utcnow()
        self._current_test.completion_end = final_completion
        self._current_test.sections_filled = sections_filled
        self._current_test.gaps_closed = gaps_closed
        self._current_test.notes = notes
        self._current_test.rating = rating

        # Save to history
        self._metrics_history.append(self._current_test)

        result = self._current_test
        self._current_test = None

        ProcessLog.success(
            "LabService",
            "Test session completed",
            details={
                "completion_change": f"{result.completion_start}% -> {result.completion_end}%",
                "total_words": result.total_words,
            }
        )

        return result

    def get_metrics_history(self) -> List[TestMetrics]:
        """Get all test metrics history."""
        return self._metrics_history.copy()

    def get_metrics_for_config(self, config_id: str) -> List[TestMetrics]:
        """Get metrics history for a specific configuration."""
        return [m for m in self._metrics_history if m.config_id == config_id]

    # =========================================================================
    # PERSISTENCE (Session State)
    # =========================================================================

    def save_to_dict(self) -> Dict[str, Any]:
        """Save entire lab state to dictionary for session persistence."""
        return {
            "feature_flags": self._feature_flags,
            "config": self._config.to_dict(),
            "configurations": {
                k: v.to_dict() for k, v in self._configurations.items()
            },
            "metrics_history": [m.to_dict() for m in self._metrics_history],
            "current_test": self._current_test.to_dict() if self._current_test else None,
            "lab_mode_active": self._lab_mode_active,
        }

    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load lab state from dictionary."""
        self._feature_flags = data.get("feature_flags", {
            f.value: v for f, v in DEFAULT_FEATURE_FLAGS.items()
        })

        config_data = data.get("config")
        if config_data:
            self._config = ConfigSettings.from_dict(config_data)

        configs_data = data.get("configurations", {})
        self._configurations = {
            k: TestConfiguration.from_dict(v) for k, v in configs_data.items()
        }

        metrics_data = data.get("metrics_history", [])
        self._metrics_history = [TestMetrics.from_dict(m) for m in metrics_data]

        current_test_data = data.get("current_test")
        if current_test_data:
            self._current_test = TestMetrics.from_dict(current_test_data)

        self._lab_mode_active = data.get("lab_mode_active", False)


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================


def create_preset_configs(lab_service: LabService) -> None:
    """Create preset test configurations."""

    # Preset 1: Tagging Only
    lab_service.set_all_feature_flags({
        FeatureFlag.REAL_TIME_TAGGING.value: True,
        FeatureFlag.CLICK_TO_RANT.value: False,
        FeatureFlag.FLASH_LABELS.value: True,
        FeatureFlag.GAP_DETECTION.value: True,
        FeatureFlag.TAG_OVERLAY.value: True,
        FeatureFlag.MULTI_PANEL_VIEW.value: False,
        FeatureFlag.COCKPIT_MODE.value: False,
        FeatureFlag.AUTO_CONSOLIDATE.value: False,
        FeatureFlag.POST_RANT_ANALYSIS.value: True,
    })
    lab_service.create_test_config(
        name="Tagging Only",
        description="Test Real-Time Tagging in isolation. Focus on tagging flow."
    )

    # Preset 2: Click-to-Rant Only
    lab_service.set_all_feature_flags({
        FeatureFlag.REAL_TIME_TAGGING.value: False,
        FeatureFlag.CLICK_TO_RANT.value: True,
        FeatureFlag.FLASH_LABELS.value: True,
        FeatureFlag.GAP_DETECTION.value: True,
        FeatureFlag.TAG_OVERLAY.value: False,
        FeatureFlag.MULTI_PANEL_VIEW.value: False,
        FeatureFlag.COCKPIT_MODE.value: False,
        FeatureFlag.AUTO_CONSOLIDATE.value: False,
        FeatureFlag.POST_RANT_ANALYSIS.value: False,
    })
    lab_service.create_test_config(
        name="Click-to-Rant Only",
        description="Test Click-to-Rant in isolation. Direct section targeting."
    )

    # Preset 3: Full Visual Mode
    lab_service.set_all_feature_flags({
        FeatureFlag.REAL_TIME_TAGGING.value: True,
        FeatureFlag.CLICK_TO_RANT.value: True,
        FeatureFlag.FLASH_LABELS.value: True,
        FeatureFlag.GAP_DETECTION.value: True,
        FeatureFlag.TAG_OVERLAY.value: True,
        FeatureFlag.MULTI_PANEL_VIEW.value: True,
        FeatureFlag.COCKPIT_MODE.value: True,
        FeatureFlag.AUTO_CONSOLIDATE.value: False,
        FeatureFlag.POST_RANT_ANALYSIS.value: True,
    })
    lab_service.create_test_config(
        name="Full Visual Mode",
        description="All visual features enabled. Maximum visibility."
    )

    # Reset to defaults after creating presets
    lab_service.reset_feature_flags()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_or_create_lab_service() -> LabService:
    """
    Get or create a LabService instance.

    In a Streamlit context, this should be called with session_state.

    Returns:
        LabService instance
    """
    return LabService()


def get_section_color(section_key: str) -> str:
    """
    Get the color for an Agent OS section.

    Used for tag overlay and multi-panel views.

    Args:
        section_key: Section key (e.g., "requirements_functional")

    Returns:
        Hex color string
    """
    section_colors = {
        # Standards - Blue
        "tech_stack": "#3b82f6",
        "architecture": "#2563eb",
        "coding_patterns": "#1d4ed8",

        # Product - Purple
        "vision": "#8b5cf6",
        "target_users": "#7c3aed",
        "use_cases": "#6d28d9",
        "roadmap": "#5b21b6",

        # Spec - Requirements - Green
        "overview": "#10b981",
        "requirements_functional": "#059669",
        "requirements_technical": "#047857",

        # Spec - User Stories - Orange
        "user_stories": "#f97316",

        # Spec - Technical - Red
        "acceptance_criteria": "#ef4444",
        "technical_spec": "#dc2626",
        "success_metrics": "#b91c1c",

        # Gaps - Yellow
        "questions": "#eab308",
    }

    return section_colors.get(section_key, "#6b7280")  # Default gray


def get_section_layer(section_key: str) -> str:
    """
    Get the layer name for an Agent OS section.

    Args:
        section_key: Section key

    Returns:
        Layer name (Standards, Product, Specs, Gaps)
    """
    standards_sections = ["tech_stack", "architecture", "coding_patterns"]
    product_sections = ["vision", "target_users", "use_cases", "roadmap"]
    gaps_sections = ["questions"]

    if section_key in standards_sections:
        return "Standards"
    elif section_key in product_sections:
        return "Product"
    elif section_key in gaps_sections:
        return "Gaps"
    else:
        return "Specs"
