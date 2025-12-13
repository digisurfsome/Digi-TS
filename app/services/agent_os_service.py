"""
Agent OS Service.

Provides Agent OS document generation, classification, and management.
Transforms stream-of-consciousness rants into structured Agent OS specifications.
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from datetime import datetime

from openai import OpenAI

from sqlalchemy.orm import Session as DBSession

from app.services.process_log import ProcessLog


# ============================================================================
# GAP DETECTION & COMPLETION TRACKING CONSTANTS
# ============================================================================

# Section weights for completion percentage calculation
SECTION_WEIGHTS = {
    "overview": 10,
    "requirements_functional": 15,
    "requirements_technical": 10,
    "user_stories": 15,
    "acceptance_criteria": 15,
    "technical_spec": 20,
    "success_metrics": 10,
    "questions": 5,
}

# Minimum items required for each section
SECTION_MINIMUMS = {
    "overview": 1,
    "requirements_functional": 2,
    "requirements_technical": 1,
    "user_stories": 2,
    "acceptance_criteria": 3,
    "technical_spec": 1,  # At least one sub-field
    "success_metrics": 1,
    "questions": 0,  # Optional
}

# Fill prompts for each section
SECTION_FILL_PROMPTS = {
    "overview": "What does this feature do? Describe it in one or two sentences.",
    "requirements_functional": "What must this feature do? List the functional requirements.",
    "requirements_technical": "What technical constraints or requirements are there?",
    "user_stories": "Who will use this? What do they want to do? (As a X, I want Y, so that Z)",
    "acceptance_criteria": "How do we know when this is done? What are the test conditions?",
    "technical_spec_api": "What API endpoints are needed?",
    "technical_spec_data": "What data models or database changes are needed?",
    "technical_spec_deps": "What dependencies or integrations are required?",
    "technical_spec_edge": "What edge cases or error conditions should be handled?",
    "success_metrics": "How will we measure if this is successful?",
    "questions": "What questions or unknowns remain?",
}


class GapSeverity(str, Enum):
    """Severity levels for gaps."""
    CRITICAL = "critical"  # Empty required section
    MINOR = "minor"  # Partial (below minimum)
    NONE = "none"  # Filled


@dataclass
class GapItem:
    """Represents a gap in the Agent OS document."""
    section: str
    subsection: Optional[str]
    severity: GapSeverity
    current_count: int
    minimum_required: int
    prompt: str
    display_name: str


# ============================================================================
# AGENT OS STRUCTURE
# ============================================================================


class AgentOSSection(str, Enum):
    """Main sections of an Agent OS document."""
    STANDARDS = "standards"
    PRODUCT = "product"
    SPECS = "specs"
    GAPS = "gaps"


class AgentOSSubsection(str, Enum):
    """Subsections within Agent OS layers."""
    # STANDARDS layer
    TECH_STACK = "tech_stack"
    ARCHITECTURE = "architecture"
    CODING_PATTERNS = "coding_patterns"

    # PRODUCT layer
    VISION = "vision"
    TARGET_USERS = "target_users"
    USE_CASES = "use_cases"
    ROADMAP = "roadmap"

    # SPECS layer
    OVERVIEW = "overview"
    REQUIREMENTS_FUNCTIONAL = "requirements_functional"
    REQUIREMENTS_TECHNICAL = "requirements_technical"
    USER_STORIES = "user_stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    TECHNICAL_SPEC = "technical_spec"
    SUCCESS_METRICS = "success_metrics"

    # GAPS
    QUESTIONS = "questions"


@dataclass
class ClassifiedItem:
    """A piece of information classified into Agent OS structure."""
    text: str
    section: AgentOSSection
    subsection: AgentOSSubsection
    confidence: float
    source_text: str
    reasoning: str


@dataclass
class AgentOSDocument:
    """Complete Agent OS document structure."""
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    # STANDARDS LAYER
    tech_stack: List[str] = field(default_factory=list)
    architecture: List[str] = field(default_factory=list)
    coding_patterns: List[str] = field(default_factory=list)

    # PRODUCT LAYER
    vision: str = ""
    target_users: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    roadmap: Dict[str, List[str]] = field(default_factory=lambda: {
        "phase_1": [],
        "phase_2": [],
        "future": []
    })

    # SPECS LAYER
    features: List[Dict[str, Any]] = field(default_factory=list)

    # GAPS
    questions: List[str] = field(default_factory=list)

    # Metadata
    completion_percentage: int = 0
    raw_rant: str = ""

    def calculate_completion(self) -> int:
        """Calculate document completion percentage using weighted sections."""
        total_weight = 0
        earned_weight = 0

        # Calculate for each feature (or overall if no features)
        if self.features:
            for feature in self.features:
                feature_scores = self._calculate_feature_completion(feature)
                for section, score in feature_scores.items():
                    weight = SECTION_WEIGHTS.get(section, 0)
                    total_weight += weight
                    earned_weight += score * weight
        else:
            # No features yet - use base structure weights
            total_weight = sum(SECTION_WEIGHTS.values())
            earned_weight = 0

        # Add standards and product layer contribution (bonus, not required)
        standards_bonus = 0
        if self.tech_stack:
            standards_bonus += 2
        if self.architecture:
            standards_bonus += 2
        if self.coding_patterns:
            standards_bonus += 1

        product_bonus = 0
        if self.vision:
            product_bonus += 3
        if self.target_users:
            product_bonus += 2
        if self.use_cases:
            product_bonus += 2
        if any(self.roadmap.values()):
            product_bonus += 3

        # Calculate percentage
        if total_weight > 0:
            base_percentage = (earned_weight / total_weight) * 100
        else:
            base_percentage = 0

        # Add bonus (up to 10% extra from standards/product)
        bonus_percentage = min((standards_bonus + product_bonus), 15)
        self.completion_percentage = min(int(base_percentage + bonus_percentage), 100)

        return self.completion_percentage

    def _calculate_feature_completion(self, feature: Dict) -> Dict[str, float]:
        """
        Calculate completion scores for a single feature.

        Returns dict of section -> score (0.0 to 1.0)
        """
        scores = {}

        # Overview
        overview = feature.get("overview", "")
        if overview and len(overview) > 10:
            scores["overview"] = 1.0
        elif overview:
            scores["overview"] = 0.5
        else:
            scores["overview"] = 0.0

        # Functional requirements
        func_reqs = feature.get("requirements_functional", [])
        min_func = SECTION_MINIMUMS["requirements_functional"]
        scores["requirements_functional"] = min(len(func_reqs) / max(min_func, 1), 1.0)

        # Technical requirements
        tech_reqs = feature.get("requirements_technical", [])
        min_tech = SECTION_MINIMUMS["requirements_technical"]
        scores["requirements_technical"] = min(len(tech_reqs) / max(min_tech, 1), 1.0)

        # User stories
        user_stories = feature.get("user_stories", [])
        min_stories = SECTION_MINIMUMS["user_stories"]
        scores["user_stories"] = min(len(user_stories) / max(min_stories, 1), 1.0)

        # Acceptance criteria
        acceptance = feature.get("acceptance_criteria", [])
        min_acceptance = SECTION_MINIMUMS["acceptance_criteria"]
        scores["acceptance_criteria"] = min(len(acceptance) / max(min_acceptance, 1), 1.0)

        # Technical spec (check sub-fields)
        tech_spec = feature.get("technical_spec", {})
        tech_spec_filled = sum(1 for v in tech_spec.values() if v)
        scores["technical_spec"] = min(tech_spec_filled / 4, 1.0)  # 4 sub-fields max

        # Success metrics
        metrics = feature.get("success_metrics", "")
        if metrics and len(metrics) > 10:
            scores["success_metrics"] = 1.0
        elif metrics:
            scores["success_metrics"] = 0.5
        else:
            scores["success_metrics"] = 0.0

        return scores

    def detect_gaps(self, feature_name: Optional[str] = None) -> List["GapItem"]:
        """
        Detect gaps in the Agent OS document.

        Args:
            feature_name: Optional specific feature to check. If None, checks all.

        Returns:
            List of GapItem objects representing missing sections.
        """
        gaps = []

        # Get features to check
        features_to_check = []
        if feature_name:
            for f in self.features:
                if f.get("name") == feature_name:
                    features_to_check = [f]
                    break
        else:
            features_to_check = self.features if self.features else [{}]

        for feature in features_to_check:
            fname = feature.get("name", "General")

            # Check Overview
            overview = feature.get("overview", "")
            if not overview:
                gaps.append(GapItem(
                    section="overview",
                    subsection=fname,
                    severity=GapSeverity.CRITICAL,
                    current_count=0,
                    minimum_required=SECTION_MINIMUMS["overview"],
                    prompt=SECTION_FILL_PROMPTS["overview"],
                    display_name=f"{fname}: Overview"
                ))

            # Check Functional Requirements
            func_reqs = feature.get("requirements_functional", [])
            min_func = SECTION_MINIMUMS["requirements_functional"]
            if len(func_reqs) == 0:
                gaps.append(GapItem(
                    section="requirements_functional",
                    subsection=fname,
                    severity=GapSeverity.CRITICAL,
                    current_count=0,
                    minimum_required=min_func,
                    prompt=SECTION_FILL_PROMPTS["requirements_functional"],
                    display_name=f"{fname}: Functional Requirements"
                ))
            elif len(func_reqs) < min_func:
                gaps.append(GapItem(
                    section="requirements_functional",
                    subsection=fname,
                    severity=GapSeverity.MINOR,
                    current_count=len(func_reqs),
                    minimum_required=min_func,
                    prompt=SECTION_FILL_PROMPTS["requirements_functional"],
                    display_name=f"{fname}: Functional Requirements"
                ))

            # Check Technical Requirements
            tech_reqs = feature.get("requirements_technical", [])
            min_tech = SECTION_MINIMUMS["requirements_technical"]
            if len(tech_reqs) == 0:
                gaps.append(GapItem(
                    section="requirements_technical",
                    subsection=fname,
                    severity=GapSeverity.MINOR,
                    current_count=0,
                    minimum_required=min_tech,
                    prompt=SECTION_FILL_PROMPTS["requirements_technical"],
                    display_name=f"{fname}: Technical Requirements"
                ))

            # Check User Stories
            user_stories = feature.get("user_stories", [])
            min_stories = SECTION_MINIMUMS["user_stories"]
            if len(user_stories) == 0:
                gaps.append(GapItem(
                    section="user_stories",
                    subsection=fname,
                    severity=GapSeverity.CRITICAL,
                    current_count=0,
                    minimum_required=min_stories,
                    prompt=SECTION_FILL_PROMPTS["user_stories"],
                    display_name=f"{fname}: User Stories"
                ))
            elif len(user_stories) < min_stories:
                gaps.append(GapItem(
                    section="user_stories",
                    subsection=fname,
                    severity=GapSeverity.MINOR,
                    current_count=len(user_stories),
                    minimum_required=min_stories,
                    prompt=SECTION_FILL_PROMPTS["user_stories"],
                    display_name=f"{fname}: User Stories"
                ))

            # Check Acceptance Criteria
            acceptance = feature.get("acceptance_criteria", [])
            min_acceptance = SECTION_MINIMUMS["acceptance_criteria"]
            if len(acceptance) == 0:
                gaps.append(GapItem(
                    section="acceptance_criteria",
                    subsection=fname,
                    severity=GapSeverity.CRITICAL,
                    current_count=0,
                    minimum_required=min_acceptance,
                    prompt=SECTION_FILL_PROMPTS["acceptance_criteria"],
                    display_name=f"{fname}: Acceptance Criteria"
                ))
            elif len(acceptance) < min_acceptance:
                gaps.append(GapItem(
                    section="acceptance_criteria",
                    subsection=fname,
                    severity=GapSeverity.MINOR,
                    current_count=len(acceptance),
                    minimum_required=min_acceptance,
                    prompt=SECTION_FILL_PROMPTS["acceptance_criteria"],
                    display_name=f"{fname}: Acceptance Criteria"
                ))

            # Check Technical Spec sub-fields
            tech_spec = feature.get("technical_spec", {})
            if not tech_spec.get("api_endpoints"):
                gaps.append(GapItem(
                    section="technical_spec",
                    subsection=f"{fname}:api_endpoints",
                    severity=GapSeverity.MINOR,
                    current_count=0,
                    minimum_required=1,
                    prompt=SECTION_FILL_PROMPTS["technical_spec_api"],
                    display_name=f"{fname}: API Endpoints"
                ))
            if not tech_spec.get("data_models"):
                gaps.append(GapItem(
                    section="technical_spec",
                    subsection=f"{fname}:data_models",
                    severity=GapSeverity.MINOR,
                    current_count=0,
                    minimum_required=1,
                    prompt=SECTION_FILL_PROMPTS["technical_spec_data"],
                    display_name=f"{fname}: Data Models"
                ))

            # Check Success Metrics
            metrics = feature.get("success_metrics", "")
            if not metrics:
                gaps.append(GapItem(
                    section="success_metrics",
                    subsection=fname,
                    severity=GapSeverity.MINOR,
                    current_count=0,
                    minimum_required=SECTION_MINIMUMS["success_metrics"],
                    prompt=SECTION_FILL_PROMPTS["success_metrics"],
                    display_name=f"{fname}: Success Metrics"
                ))

        return gaps

    def get_section_status(self, feature_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get status for each section (empty, partial, complete).

        Used for Flash Labels display.

        Args:
            feature_name: Optional specific feature to check.

        Returns:
            Dict mapping section name to status string.
        """
        statuses = {}

        # Get the feature to check
        feature = {}
        if feature_name:
            for f in self.features:
                if f.get("name") == feature_name:
                    feature = f
                    break
        elif self.features:
            feature = self.features[0]  # Default to first feature

        # Overview
        overview = feature.get("overview", "")
        if overview and len(overview) > 10:
            statuses["Overview"] = "complete"
        elif overview:
            statuses["Overview"] = "partial"
        else:
            statuses["Overview"] = "empty"

        # Requirements (Functional)
        func_reqs = feature.get("requirements_functional", [])
        min_func = SECTION_MINIMUMS["requirements_functional"]
        if len(func_reqs) >= min_func:
            statuses["Requirements (Functional)"] = "complete"
        elif func_reqs:
            statuses["Requirements (Functional)"] = "partial"
        else:
            statuses["Requirements (Functional)"] = "empty"

        # Requirements (Technical)
        tech_reqs = feature.get("requirements_technical", [])
        min_tech = SECTION_MINIMUMS["requirements_technical"]
        if len(tech_reqs) >= min_tech:
            statuses["Requirements (Technical)"] = "complete"
        elif tech_reqs:
            statuses["Requirements (Technical)"] = "partial"
        else:
            statuses["Requirements (Technical)"] = "empty"

        # User Stories
        user_stories = feature.get("user_stories", [])
        min_stories = SECTION_MINIMUMS["user_stories"]
        if len(user_stories) >= min_stories:
            statuses["User Stories"] = "complete"
        elif user_stories:
            statuses["User Stories"] = "partial"
        else:
            statuses["User Stories"] = "empty"

        # Acceptance Criteria
        acceptance = feature.get("acceptance_criteria", [])
        min_acceptance = SECTION_MINIMUMS["acceptance_criteria"]
        if len(acceptance) >= min_acceptance:
            statuses["Acceptance Criteria"] = "complete"
        elif acceptance:
            statuses["Acceptance Criteria"] = "partial"
        else:
            statuses["Acceptance Criteria"] = "empty"

        # Technical Specification
        tech_spec = feature.get("technical_spec", {})
        tech_filled = sum(1 for v in tech_spec.values() if v)
        if tech_filled >= 3:
            statuses["Technical Specification"] = "complete"
        elif tech_filled > 0:
            statuses["Technical Specification"] = "partial"
        else:
            statuses["Technical Specification"] = "empty"

        # Success Metrics
        metrics = feature.get("success_metrics", "")
        if metrics and len(metrics) > 10:
            statuses["Success Metrics"] = "complete"
        elif metrics:
            statuses["Success Metrics"] = "partial"
        else:
            statuses["Success Metrics"] = "empty"

        return statuses

    def get_gap_summary(self) -> Dict[str, Any]:
        """
        Get a summary of gaps for display.

        Returns:
            Dict with total_gaps, critical_count, minor_count, gaps list.
        """
        gaps = self.detect_gaps()
        critical = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
        minor = [g for g in gaps if g.severity == GapSeverity.MINOR]

        return {
            "total_gaps": len(gaps),
            "critical_count": len(critical),
            "minor_count": len(minor),
            "gaps": gaps,
            "critical_gaps": critical,
            "minor_gaps": minor,
        }

    def to_markdown(self) -> str:
        """Generate markdown representation of the Agent OS document."""
        self.calculate_completion()

        lines = [
            f"# Agent OS: {self.name}",
            "",
            "## STANDARDS LAYER",
            "",
            "### Technology Stack",
        ]

        if self.tech_stack:
            for item in self.tech_stack:
                lines.append(f"- {item}")
        else:
            lines.append("- *(Not yet defined)*")

        lines.extend([
            "",
            "### Architecture",
        ])

        if self.architecture:
            for item in self.architecture:
                lines.append(f"- {item}")
        else:
            lines.append("- *(Not yet defined)*")

        lines.extend([
            "",
            "### Coding Patterns",
        ])

        if self.coding_patterns:
            for item in self.coding_patterns:
                lines.append(f"- {item}")
        else:
            lines.append("- *(Not yet defined)*")

        lines.extend([
            "",
            "---",
            "",
            "## PRODUCT LAYER",
            "",
            "### Vision",
        ])

        lines.append(self.vision if self.vision else "*(Not yet defined)*")

        lines.extend([
            "",
            "### Target Users",
        ])

        if self.target_users:
            for user in self.target_users:
                lines.append(f"- {user}")
        else:
            lines.append("- *(Not yet defined)*")

        lines.extend([
            "",
            "### Core Use Cases",
        ])

        if self.use_cases:
            for i, uc in enumerate(self.use_cases, 1):
                lines.append(f"{i}. {uc}")
        else:
            lines.append("1. *(Not yet defined)*")

        lines.extend([
            "",
            "### Roadmap",
        ])

        if self.roadmap.get("phase_1"):
            lines.append("- **Phase 1 (Current):**")
            for item in self.roadmap["phase_1"]:
                lines.append(f"  - {item}")

        if self.roadmap.get("phase_2"):
            lines.append("- **Phase 2 (Next):**")
            for item in self.roadmap["phase_2"]:
                lines.append(f"  - {item}")

        if self.roadmap.get("future"):
            lines.append("- **Future:**")
            for item in self.roadmap["future"]:
                lines.append(f"  - {item}")

        if not any(self.roadmap.values()):
            lines.append("- *(Not yet defined)*")

        lines.extend([
            "",
            "---",
            "",
            "## SPEC LAYER",
            "",
        ])

        if self.features:
            for feature in self.features:
                lines.extend([
                    f"### Feature: {feature.get('name', 'Unnamed')}",
                    "",
                    "#### Overview",
                    feature.get('overview', '*(Not yet defined)*'),
                    "",
                    "#### Requirements",
                    "",
                    "**Functional:**",
                ])

                func_reqs = feature.get('requirements_functional', [])
                if func_reqs:
                    for i, req in enumerate(func_reqs, 1):
                        lines.append(f"{i}. {req}")
                else:
                    lines.append("1. *(Not yet defined)*")

                lines.extend([
                    "",
                    "**Technical:**",
                ])

                tech_reqs = feature.get('requirements_technical', [])
                if tech_reqs:
                    for i, req in enumerate(tech_reqs, 1):
                        lines.append(f"{i}. {req}")
                else:
                    lines.append("1. *(Not yet defined)*")

                lines.extend([
                    "",
                    "#### User Stories",
                ])

                user_stories = feature.get('user_stories', [])
                if user_stories:
                    for story in user_stories:
                        lines.append(f"- {story}")
                else:
                    lines.append("- *(Not yet defined)*")

                lines.extend([
                    "",
                    "#### Acceptance Criteria",
                ])

                acceptance = feature.get('acceptance_criteria', [])
                if acceptance:
                    for criterion in acceptance:
                        lines.append(f"- [ ] {criterion}")
                else:
                    lines.append("- [ ] *(Not yet defined)*")

                lines.extend([
                    "",
                    "#### Technical Specification",
                ])

                tech_spec = feature.get('technical_spec', {})
                lines.append(f"- **API Endpoints:** {tech_spec.get('api_endpoints', '*(Not yet defined)*')}")
                lines.append(f"- **Data Models:** {tech_spec.get('data_models', '*(Not yet defined)*')}")
                lines.append(f"- **Dependencies:** {tech_spec.get('dependencies', '*(Not yet defined)*')}")
                lines.append(f"- **Edge Cases:** {tech_spec.get('edge_cases', '*(Not yet defined)*')}")

                lines.extend([
                    "",
                    "#### Success Metrics",
                    feature.get('success_metrics', '*(Not yet defined)*'),
                    "",
                ])
        else:
            lines.extend([
                "### Feature: *(No features defined yet)*",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## GAPS / QUESTIONS",
            "",
        ])

        if self.questions:
            for q in self.questions:
                lines.append(f"- [ ] {q}")
        else:
            lines.append("- [ ] *(No gaps identified yet)*")

        lines.extend([
            "",
            f"## COMPLETION: {self.completion_percentage}%",
        ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for storage."""
        self.calculate_completion()
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "standards": {
                "tech_stack": self.tech_stack,
                "architecture": self.architecture,
                "coding_patterns": self.coding_patterns,
            },
            "product": {
                "vision": self.vision,
                "target_users": self.target_users,
                "use_cases": self.use_cases,
                "roadmap": self.roadmap,
            },
            "specs": {
                "features": self.features,
            },
            "gaps": {
                "questions": self.questions,
            },
            "completion_percentage": self.completion_percentage,
            "raw_rant": self.raw_rant,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentOSDocument":
        """Create document from dictionary."""
        doc = cls(name=data.get("name", "Untitled"))

        standards = data.get("standards", {})
        doc.tech_stack = standards.get("tech_stack", [])
        doc.architecture = standards.get("architecture", [])
        doc.coding_patterns = standards.get("coding_patterns", [])

        product = data.get("product", {})
        doc.vision = product.get("vision", "")
        doc.target_users = product.get("target_users", [])
        doc.use_cases = product.get("use_cases", [])
        doc.roadmap = product.get("roadmap", {"phase_1": [], "phase_2": [], "future": []})

        specs = data.get("specs", {})
        doc.features = specs.get("features", [])

        gaps = data.get("gaps", {})
        doc.questions = gaps.get("questions", [])

        doc.raw_rant = data.get("raw_rant", "")
        doc.calculate_completion()

        return doc


# ============================================================================
# CLASSIFICATION LOGIC
# ============================================================================


CLASSIFICATION_PROMPT = """You are analyzing conversation text to classify information into an Agent OS document structure.

Agent OS has THREE LAYERS:

1. STANDARDS LAYER - Technical decisions
   - tech_stack: Technologies, frameworks, languages (e.g., "React", "PostgreSQL", "Python")
   - architecture: Structural decisions (e.g., "microservices", "monorepo", "serverless")
   - coding_patterns: Style/patterns (e.g., "TDD", "functional programming", "DRY")

2. PRODUCT LAYER - What and why
   - vision: Ultimate goal, problem being solved
   - target_users: Who this is for
   - use_cases: What users need to do
   - roadmap: Phases of development

3. SPECS LAYER - How (detailed)
   - feature_name: Name of a specific feature
   - overview: Brief feature description
   - requirements_functional: What it must do
   - requirements_technical: Technical constraints
   - user_stories: "As a X, I want Y, so that Z"
   - acceptance_criteria: How to verify it works
   - technical_spec: API endpoints, data models, dependencies, edge cases
   - success_metrics: How to measure success

4. GAPS - Questions or missing information

Analyze this text and extract ALL relevant pieces of information:

---
{text}
---

Return a JSON object with this structure:
{{
  "items": [
    {{
      "text": "the extracted/summarized information",
      "section": "standards|product|specs|gaps",
      "subsection": "tech_stack|architecture|coding_patterns|vision|target_users|use_cases|roadmap|feature_name|overview|requirements_functional|requirements_technical|user_stories|acceptance_criteria|technical_spec|success_metrics|questions",
      "confidence": 0.0-1.0,
      "source_text": "original text snippet",
      "reasoning": "why this classification"
    }}
  ],
  "suggested_name": "suggested project/feature name based on content"
}}

IMPORTANT:
- Extract MULTIPLE items if the text contains multiple pieces of information
- Be thorough - don't miss relevant information
- Use confidence scores: 0.9+ for explicit statements, 0.7-0.9 for implied, 0.5-0.7 for inferred
- If a piece of info fits multiple categories, include it in the most specific one
- For features, group related requirements under a feature_name first

Return ONLY valid JSON, no other text."""


def classify_text(
    text: str,
    openai_api_key: str,
    model: str = "gpt-4-turbo-preview"
) -> Tuple[List[ClassifiedItem], str]:
    """
    Classify text into Agent OS sections.

    Args:
        text: Text to classify
        openai_api_key: OpenAI API key
        model: Model to use

    Returns:
        Tuple of (list of ClassifiedItems, suggested name)
    """
    if not openai_api_key:
        ProcessLog.warning("AgentOS", "No API key for classification")
        return [], ""

    if not text or len(text.strip()) < 10:
        return [], ""

    prompt = CLASSIFICATION_PROMPT.format(text=text)

    try:
        ProcessLog.info("AgentOS", "Classifying text into Agent OS structure")
        start_time = time.time()

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a JSON-only response bot. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        duration_ms = (time.time() - start_time) * 1000
        response_text = response.choices[0].message.content.strip()

        # Parse JSON response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        data = json.loads(response_text)

        items = []
        for item_data in data.get("items", []):
            try:
                section_str = item_data.get("section", "").lower()
                subsection_str = item_data.get("subsection", "").lower()

                # Map to enums
                section = AgentOSSection(section_str) if section_str in [s.value for s in AgentOSSection] else AgentOSSection.GAPS

                subsection_map = {s.value: s for s in AgentOSSubsection}
                subsection = subsection_map.get(subsection_str, AgentOSSubsection.QUESTIONS)

                item = ClassifiedItem(
                    text=item_data.get("text", ""),
                    section=section,
                    subsection=subsection,
                    confidence=float(item_data.get("confidence", 0.5)),
                    source_text=item_data.get("source_text", ""),
                    reasoning=item_data.get("reasoning", "")
                )

                if item.confidence >= 0.5:
                    items.append(item)

            except (KeyError, ValueError) as e:
                ProcessLog.warning("AgentOS", f"Skipped invalid item: {e}")
                continue

        suggested_name = data.get("suggested_name", "Untitled Project")

        ProcessLog.success(
            "AgentOS",
            f"Classified {len(items)} items into Agent OS structure",
            details={"count": len(items), "suggested_name": suggested_name},
            duration_ms=duration_ms
        )

        return items, suggested_name

    except json.JSONDecodeError as e:
        ProcessLog.error("AgentOS", f"Failed to parse classification JSON: {e}")
        return [], ""
    except Exception as e:
        ProcessLog.error("AgentOS", f"Classification failed: {str(e)}")
        return [], ""


def build_document_from_items(
    items: List[ClassifiedItem],
    name: str,
    raw_rant: str = ""
) -> AgentOSDocument:
    """
    Build an AgentOSDocument from classified items.

    Args:
        items: List of classified items
        name: Document name
        raw_rant: Original rant text

    Returns:
        AgentOSDocument
    """
    doc = AgentOSDocument(name=name, raw_rant=raw_rant)

    current_feature = None
    features_dict: Dict[str, Dict] = {}

    for item in items:
        if item.section == AgentOSSection.STANDARDS:
            if item.subsection == AgentOSSubsection.TECH_STACK:
                doc.tech_stack.append(item.text)
            elif item.subsection == AgentOSSubsection.ARCHITECTURE:
                doc.architecture.append(item.text)
            elif item.subsection == AgentOSSubsection.CODING_PATTERNS:
                doc.coding_patterns.append(item.text)

        elif item.section == AgentOSSection.PRODUCT:
            if item.subsection == AgentOSSubsection.VISION:
                doc.vision = item.text if not doc.vision else f"{doc.vision}\n{item.text}"
            elif item.subsection == AgentOSSubsection.TARGET_USERS:
                doc.target_users.append(item.text)
            elif item.subsection == AgentOSSubsection.USE_CASES:
                doc.use_cases.append(item.text)
            elif item.subsection == AgentOSSubsection.ROADMAP:
                # Try to determine phase from text
                text_lower = item.text.lower()
                if "phase 1" in text_lower or "first" in text_lower or "current" in text_lower:
                    doc.roadmap["phase_1"].append(item.text)
                elif "phase 2" in text_lower or "next" in text_lower:
                    doc.roadmap["phase_2"].append(item.text)
                else:
                    doc.roadmap["future"].append(item.text)

        elif item.section == AgentOSSection.SPECS:
            # Handle feature-specific items
            subsection_str = item.subsection.value if hasattr(item.subsection, 'value') else str(item.subsection)

            if subsection_str == "feature_name":
                current_feature = item.text
                if current_feature not in features_dict:
                    features_dict[current_feature] = {
                        "name": current_feature,
                        "overview": "",
                        "requirements_functional": [],
                        "requirements_technical": [],
                        "user_stories": [],
                        "acceptance_criteria": [],
                        "technical_spec": {},
                        "success_metrics": ""
                    }
            elif current_feature and current_feature in features_dict:
                feature = features_dict[current_feature]
                if subsection_str == "overview":
                    feature["overview"] = item.text
                elif subsection_str == "requirements_functional":
                    feature["requirements_functional"].append(item.text)
                elif subsection_str == "requirements_technical":
                    feature["requirements_technical"].append(item.text)
                elif subsection_str == "user_stories":
                    feature["user_stories"].append(item.text)
                elif subsection_str == "acceptance_criteria":
                    feature["acceptance_criteria"].append(item.text)
                elif subsection_str == "technical_spec":
                    # Parse technical spec from text
                    if "api" in item.text.lower() or "endpoint" in item.text.lower():
                        feature["technical_spec"]["api_endpoints"] = item.text
                    elif "model" in item.text.lower() or "data" in item.text.lower():
                        feature["technical_spec"]["data_models"] = item.text
                    elif "depend" in item.text.lower():
                        feature["technical_spec"]["dependencies"] = item.text
                    elif "edge" in item.text.lower() or "error" in item.text.lower():
                        feature["technical_spec"]["edge_cases"] = item.text
                    else:
                        feature["technical_spec"]["other"] = item.text
                elif subsection_str == "success_metrics":
                    feature["success_metrics"] = item.text
            else:
                # No current feature - create a generic one
                if "General" not in features_dict:
                    features_dict["General"] = {
                        "name": "General",
                        "overview": "",
                        "requirements_functional": [],
                        "requirements_technical": [],
                        "user_stories": [],
                        "acceptance_criteria": [],
                        "technical_spec": {},
                        "success_metrics": ""
                    }
                feature = features_dict["General"]
                if subsection_str == "requirements_functional":
                    feature["requirements_functional"].append(item.text)
                elif subsection_str == "requirements_technical":
                    feature["requirements_technical"].append(item.text)
                elif subsection_str == "user_stories":
                    feature["user_stories"].append(item.text)
                elif subsection_str == "acceptance_criteria":
                    feature["acceptance_criteria"].append(item.text)

        elif item.section == AgentOSSection.GAPS:
            doc.questions.append(item.text)

    # Convert features dict to list
    doc.features = list(features_dict.values())

    doc.calculate_completion()
    return doc


def generate_agent_os_from_rant(
    rant_text: str,
    openai_api_key: str,
    project_name: Optional[str] = None,
    model: str = "gpt-4-turbo-preview"
) -> AgentOSDocument:
    """
    Generate complete Agent OS document from raw rant.

    Args:
        rant_text: Raw rant/brainstorm text
        openai_api_key: OpenAI API key
        project_name: Optional project name (will be auto-detected if not provided)
        model: Model to use

    Returns:
        Complete AgentOSDocument
    """
    ProcessLog.info("AgentOS", "Generating Agent OS document from rant")

    # Classify the text
    items, suggested_name = classify_text(rant_text, openai_api_key, model)

    # Use provided name or suggested name
    name = project_name or suggested_name or "Untitled Project"

    # Build document
    doc = build_document_from_items(items, name, raw_rant=rant_text)

    ProcessLog.success(
        "AgentOS",
        f"Generated Agent OS document: {name} ({doc.completion_percentage}% complete)",
        details={"items": len(items), "completion": doc.completion_percentage}
    )

    return doc


def create_empty_template(name: str = "New Project") -> AgentOSDocument:
    """
    Create an empty Agent OS template.

    Args:
        name: Project name

    Returns:
        Empty AgentOSDocument
    """
    return AgentOSDocument(name=name)


def get_section_icon(section: AgentOSSection) -> str:
    """Get emoji icon for Agent OS section."""
    icons = {
        AgentOSSection.STANDARDS: "🔧",
        AgentOSSection.PRODUCT: "🎯",
        AgentOSSection.SPECS: "📋",
        AgentOSSection.GAPS: "❓",
    }
    return icons.get(section, "📄")


def get_subsection_icon(subsection: AgentOSSubsection) -> str:
    """Get emoji icon for Agent OS subsection."""
    icons = {
        AgentOSSubsection.TECH_STACK: "💻",
        AgentOSSubsection.ARCHITECTURE: "🏗️",
        AgentOSSubsection.CODING_PATTERNS: "📐",
        AgentOSSubsection.VISION: "🌟",
        AgentOSSubsection.TARGET_USERS: "👥",
        AgentOSSubsection.USE_CASES: "📝",
        AgentOSSubsection.ROADMAP: "🗺️",
        AgentOSSubsection.OVERVIEW: "📖",
        AgentOSSubsection.REQUIREMENTS_FUNCTIONAL: "✅",
        AgentOSSubsection.REQUIREMENTS_TECHNICAL: "⚙️",
        AgentOSSubsection.USER_STORIES: "👤",
        AgentOSSubsection.ACCEPTANCE_CRITERIA: "☑️",
        AgentOSSubsection.TECHNICAL_SPEC: "🔩",
        AgentOSSubsection.SUCCESS_METRICS: "📊",
        AgentOSSubsection.QUESTIONS: "❓",
    }
    return icons.get(subsection, "📄")


def get_classification_summary(items: List[ClassifiedItem]) -> Dict[str, int]:
    """
    Get summary of classifications by section.

    Args:
        items: List of classified items

    Returns:
        Dict with section counts
    """
    summary = {
        AgentOSSection.STANDARDS.value: 0,
        AgentOSSection.PRODUCT.value: 0,
        AgentOSSection.SPECS.value: 0,
        AgentOSSection.GAPS.value: 0,
    }

    for item in items:
        summary[item.section.value] += 1

    return summary


# ============================================================================
# RAW RANT PRESERVATION
# ============================================================================


def save_raw_rant(
    db: DBSession,
    project_id: int,
    content: str,
    session_id: Optional[int] = None,
    source_type: str = "chat",
    agent_os_doc: Optional[Dict] = None
) -> Any:
    """
    Save raw rant to database.

    The raw rant is SACRED - it should never be modified after creation.

    Args:
        db: Database session
        project_id: Project ID
        content: Raw rant content
        session_id: Optional chat session ID
        source_type: Source of the rant (chat, manual, voice)
        agent_os_doc: Optional generated Agent OS document as dict

    Returns:
        Created RawRant object
    """
    from app.core.models import RawRant

    word_count = len(content.split())

    raw_rant = RawRant(
        project_id=project_id,
        session_id=session_id,
        content=content,
        source_type=source_type,
        word_count=word_count,
        agent_os_doc=agent_os_doc
    )

    db.add(raw_rant)
    db.commit()
    db.refresh(raw_rant)

    ProcessLog.success(
        "AgentOS",
        f"Saved raw rant ({word_count} words)",
        details={"id": raw_rant.id, "project_id": project_id}
    )

    return raw_rant


def get_raw_rants(
    db: DBSession,
    project_id: int,
    session_id: Optional[int] = None,
    limit: int = 50
) -> List[Any]:
    """
    Get raw rants for a project.

    Args:
        db: Database session
        project_id: Project ID
        session_id: Optional filter by session
        limit: Maximum number to return

    Returns:
        List of RawRant objects
    """
    from app.core.models import RawRant

    query = db.query(RawRant).filter(RawRant.project_id == project_id)

    if session_id:
        query = query.filter(RawRant.session_id == session_id)

    return query.order_by(RawRant.created_at.desc()).limit(limit).all()


def get_raw_rant_by_id(db: DBSession, rant_id: int) -> Optional[Any]:
    """
    Get a specific raw rant by ID.

    Args:
        db: Database session
        rant_id: Raw rant ID

    Returns:
        RawRant object or None
    """
    from app.core.models import RawRant

    return db.query(RawRant).filter(RawRant.id == rant_id).first()


def get_full_conversation_text(
    db: DBSession,
    session_id: int,
    include_warmup: bool = False
) -> str:
    """
    Get full conversation text from a chat session.

    Args:
        db: Database session
        session_id: Chat session ID
        include_warmup: Whether to include warmup messages

    Returns:
        Concatenated conversation text
    """
    from app.core.models import ChatMessage

    query = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.role != "system"
    )

    if not include_warmup:
        query = query.filter(ChatMessage.is_warmup == False)

    messages = query.order_by(ChatMessage.created_at).all()

    text_parts = []
    for msg in messages:
        role = "User" if msg.role.value == "user" else "AI"
        text_parts.append(f"{role}: {msg.content}")

    return "\n\n".join(text_parts)


# ============================================================================
# GAP DETECTION & FILL REQUEST FUNCTIONS
# ============================================================================


def detect_gaps(doc: AgentOSDocument, feature_name: Optional[str] = None) -> List[GapItem]:
    """
    Detect gaps in an Agent OS document.

    Wrapper function for AgentOSDocument.detect_gaps().

    Args:
        doc: AgentOSDocument to analyze
        feature_name: Optional specific feature to check

    Returns:
        List of GapItem objects
    """
    return doc.detect_gaps(feature_name)


def calculate_completion_percentage(doc: AgentOSDocument) -> int:
    """
    Calculate completion percentage for an Agent OS document.

    Wrapper function for AgentOSDocument.calculate_completion().

    Args:
        doc: AgentOSDocument to analyze

    Returns:
        Completion percentage (0-100)
    """
    return doc.calculate_completion()


def get_completion_color(percentage: int) -> str:
    """
    Get color code based on completion percentage.

    Args:
        percentage: Completion percentage (0-100)

    Returns:
        Color string for UI display
    """
    if percentage < 50:
        return "red"
    elif percentage < 80:
        return "orange"
    else:
        return "green"


def generate_fill_prompts(
    doc: AgentOSDocument,
    openai_api_key: str,
    model: str = "gpt-4-turbo-preview",
    max_questions: int = 5
) -> List[Dict[str, str]]:
    """
    Generate AI-powered questions to help fill gaps.

    Args:
        doc: AgentOSDocument to analyze
        openai_api_key: OpenAI API key
        model: Model to use
        max_questions: Maximum number of questions to generate

    Returns:
        List of dicts with 'section', 'question', 'context' keys
    """
    gaps = doc.detect_gaps()

    if not gaps:
        return []

    # Prioritize critical gaps first
    critical_gaps = [g for g in gaps if g.severity == GapSeverity.CRITICAL]
    minor_gaps = [g for g in gaps if g.severity == GapSeverity.MINOR]

    # Select gaps to generate questions for
    selected_gaps = (critical_gaps + minor_gaps)[:max_questions]

    if not openai_api_key:
        # Return static prompts if no API key
        return [
            {
                "section": gap.display_name,
                "question": gap.prompt,
                "context": f"This section is {gap.severity.value}. Currently has {gap.current_count}/{gap.minimum_required} items."
            }
            for gap in selected_gaps
        ]

    # Generate AI-powered questions
    try:
        client = OpenAI(api_key=openai_api_key)

        # Build context from existing document
        existing_context = []
        if doc.vision:
            existing_context.append(f"Vision: {doc.vision}")
        if doc.features:
            for f in doc.features:
                if f.get("overview"):
                    existing_context.append(f"Feature '{f.get('name')}': {f.get('overview')}")

        context_str = "\n".join(existing_context) if existing_context else "No existing context available."

        gap_descriptions = "\n".join([
            f"- {gap.display_name}: {gap.prompt}"
            for gap in selected_gaps
        ])

        prompt = f"""Based on this project context:
{context_str}

The following gaps need to be filled:
{gap_descriptions}

Generate {len(selected_gaps)} specific, actionable questions that would help gather the missing information.
Each question should be conversational and easy to answer verbally.

Return as JSON array:
[
  {{"section": "section name", "question": "the question", "context": "why this matters"}}
]

Return ONLY valid JSON, no other text."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful product manager asking clarifying questions. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        response_text = response.choices[0].message.content.strip()

        # Parse JSON
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        questions = json.loads(response_text)

        ProcessLog.success(
            "AgentOS",
            f"Generated {len(questions)} fill prompts for gaps",
            details={"gap_count": len(selected_gaps)}
        )

        return questions

    except Exception as e:
        ProcessLog.warning("AgentOS", f"Failed to generate AI fill prompts: {e}")
        # Fall back to static prompts
        return [
            {
                "section": gap.display_name,
                "question": gap.prompt,
                "context": f"This section is {gap.severity.value}. Currently has {gap.current_count}/{gap.minimum_required} items."
            }
            for gap in selected_gaps
        ]


def process_fill_response(
    doc: AgentOSDocument,
    section: str,
    response_text: str,
    openai_api_key: str,
    model: str = "gpt-4-turbo-preview"
) -> AgentOSDocument:
    """
    Process a user's response to a fill prompt and update the document.

    Args:
        doc: AgentOSDocument to update
        section: Section being filled
        response_text: User's response text
        openai_api_key: OpenAI API key
        model: Model to use

    Returns:
        Updated AgentOSDocument
    """
    if not response_text.strip():
        return doc

    # Classify the response and add to appropriate section
    items, _ = classify_text(response_text, openai_api_key, model)

    if not items:
        # If classification failed, try to add directly based on section hint
        ProcessLog.warning("AgentOS", "Classification returned no items, adding response directly")

        # Parse section name to determine where to add
        section_lower = section.lower()

        if doc.features:
            feature = doc.features[0]  # Default to first feature
        else:
            # Create a new feature
            doc.features.append({
                "name": "General",
                "overview": "",
                "requirements_functional": [],
                "requirements_technical": [],
                "user_stories": [],
                "acceptance_criteria": [],
                "technical_spec": {},
                "success_metrics": ""
            })
            feature = doc.features[0]

        if "overview" in section_lower:
            feature["overview"] = response_text.strip()
        elif "functional" in section_lower:
            feature["requirements_functional"].append(response_text.strip())
        elif "technical req" in section_lower:
            feature["requirements_technical"].append(response_text.strip())
        elif "user stor" in section_lower:
            feature["user_stories"].append(response_text.strip())
        elif "acceptance" in section_lower:
            feature["acceptance_criteria"].append(response_text.strip())
        elif "api" in section_lower:
            feature["technical_spec"]["api_endpoints"] = response_text.strip()
        elif "data model" in section_lower:
            feature["technical_spec"]["data_models"] = response_text.strip()
        elif "metric" in section_lower:
            feature["success_metrics"] = response_text.strip()

    else:
        # Merge classified items into the document
        doc = _merge_items_into_document(doc, items)

    doc.calculate_completion()
    return doc


def _merge_items_into_document(doc: AgentOSDocument, items: List[ClassifiedItem]) -> AgentOSDocument:
    """
    Merge new classified items into an existing document.

    Args:
        doc: Existing AgentOSDocument
        items: New classified items to merge

    Returns:
        Updated AgentOSDocument
    """
    # Ensure at least one feature exists
    if not doc.features:
        doc.features.append({
            "name": "General",
            "overview": "",
            "requirements_functional": [],
            "requirements_technical": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "technical_spec": {},
            "success_metrics": ""
        })

    current_feature = doc.features[0]  # Default to first feature

    for item in items:
        if item.section == AgentOSSection.STANDARDS:
            if item.subsection == AgentOSSubsection.TECH_STACK:
                if item.text not in doc.tech_stack:
                    doc.tech_stack.append(item.text)
            elif item.subsection == AgentOSSubsection.ARCHITECTURE:
                if item.text not in doc.architecture:
                    doc.architecture.append(item.text)
            elif item.subsection == AgentOSSubsection.CODING_PATTERNS:
                if item.text not in doc.coding_patterns:
                    doc.coding_patterns.append(item.text)

        elif item.section == AgentOSSection.PRODUCT:
            if item.subsection == AgentOSSubsection.VISION:
                if not doc.vision:
                    doc.vision = item.text
                elif item.text not in doc.vision:
                    doc.vision = f"{doc.vision}\n{item.text}"
            elif item.subsection == AgentOSSubsection.TARGET_USERS:
                if item.text not in doc.target_users:
                    doc.target_users.append(item.text)
            elif item.subsection == AgentOSSubsection.USE_CASES:
                if item.text not in doc.use_cases:
                    doc.use_cases.append(item.text)

        elif item.section == AgentOSSection.SPECS:
            subsection_str = item.subsection.value if hasattr(item.subsection, 'value') else str(item.subsection)

            if subsection_str == "overview":
                if not current_feature.get("overview"):
                    current_feature["overview"] = item.text
            elif subsection_str == "requirements_functional":
                if item.text not in current_feature.get("requirements_functional", []):
                    current_feature.setdefault("requirements_functional", []).append(item.text)
            elif subsection_str == "requirements_technical":
                if item.text not in current_feature.get("requirements_technical", []):
                    current_feature.setdefault("requirements_technical", []).append(item.text)
            elif subsection_str == "user_stories":
                if item.text not in current_feature.get("user_stories", []):
                    current_feature.setdefault("user_stories", []).append(item.text)
            elif subsection_str == "acceptance_criteria":
                if item.text not in current_feature.get("acceptance_criteria", []):
                    current_feature.setdefault("acceptance_criteria", []).append(item.text)
            elif subsection_str == "success_metrics":
                if not current_feature.get("success_metrics"):
                    current_feature["success_metrics"] = item.text

        elif item.section == AgentOSSection.GAPS:
            if item.text not in doc.questions:
                doc.questions.append(item.text)

    return doc


def get_flash_label_sections() -> List[str]:
    """
    Get list of sections for Flash Labels display.

    Returns:
        List of section names for Flash Labels
    """
    return [
        "Overview",
        "Requirements (Functional)",
        "Requirements (Technical)",
        "User Stories",
        "Acceptance Criteria",
        "Technical Specification",
        "Success Metrics"
    ]


# ============================================================================
# VOICE RANT HANDLING (Phase 2B)
# ============================================================================


# Section key mapping for voice input
VOICE_SECTION_MAP = {
    "Overview": "overview",
    "Requirements (Functional)": "requirements_functional",
    "Requirements (Technical)": "requirements_technical",
    "User Stories": "user_stories",
    "Acceptance Criteria": "acceptance_criteria",
    "Technical Specification": "technical_spec",
    "Success Metrics": "success_metrics",
    "Questions": "questions",
    # Shorter versions
    "Functional Req": "requirements_functional",
    "Technical Req": "requirements_technical",
    "Tech Spec": "technical_spec",
    "Metrics": "success_metrics",
}


def save_voice_rant(
    db: DBSession,
    project_id: int,
    raw_transcript: str,
    total_duration: float,
    mode: str = "real_time_tag",
    target_section: Optional[str] = None,
    tag_events: Optional[List[Dict]] = None,
    tagged_segments: Optional[List[Dict]] = None,
    whisper_segments: Optional[List[Dict]] = None,
    session_id: Optional[int] = None,
    agent_os_doc: Optional[Dict] = None
) -> Any:
    """
    Save a voice rant to database.

    Args:
        db: Database session
        project_id: Project ID
        raw_transcript: Full transcribed text (SACRED - never modified)
        total_duration: Recording duration in seconds
        mode: Voice input mode (click_to_rant or real_time_tag)
        target_section: Target section for click_to_rant mode
        tag_events: List of tag events [{section, timestamp}, ...]
        tagged_segments: List of tagged segments [{section, text, start_time, end_time}, ...]
        whisper_segments: Raw Whisper API segments
        session_id: Optional chat session ID
        agent_os_doc: Optional generated Agent OS document

    Returns:
        Created VoiceRant object
    """
    from app.core.models import VoiceRant, VoiceInputMode

    word_count = len(raw_transcript.split()) if raw_transcript else 0

    voice_mode = VoiceInputMode.CLICK_TO_RANT if mode == "click_to_rant" else VoiceInputMode.REAL_TIME_TAG

    voice_rant = VoiceRant(
        project_id=project_id,
        session_id=session_id,
        raw_transcript=raw_transcript,
        total_duration=total_duration,
        word_count=word_count,
        mode=voice_mode,
        target_section=target_section,
        tag_events=tag_events,
        tagged_segments=tagged_segments,
        whisper_segments=whisper_segments,
        agent_os_doc=agent_os_doc
    )

    db.add(voice_rant)
    db.commit()
    db.refresh(voice_rant)

    ProcessLog.success(
        "AgentOS",
        f"Saved voice rant ({word_count} words, {total_duration:.1f}s)",
        details={"id": voice_rant.id, "project_id": project_id, "mode": mode}
    )

    return voice_rant


def get_voice_rants(
    db: DBSession,
    project_id: int,
    session_id: Optional[int] = None,
    limit: int = 50
) -> List[Any]:
    """
    Get voice rants for a project.

    Args:
        db: Database session
        project_id: Project ID
        session_id: Optional filter by session
        limit: Maximum number to return

    Returns:
        List of VoiceRant objects
    """
    from app.core.models import VoiceRant

    query = db.query(VoiceRant).filter(VoiceRant.project_id == project_id)

    if session_id:
        query = query.filter(VoiceRant.session_id == session_id)

    return query.order_by(VoiceRant.created_at.desc()).limit(limit).all()


def add_tagged_content_to_document(
    doc: AgentOSDocument,
    section_key: str,
    content: str,
    feature_name: Optional[str] = None
) -> AgentOSDocument:
    """
    Add voice-transcribed content to a specific Agent OS section.

    Used by Click-to-Rant to add content to a target section.

    Args:
        doc: AgentOSDocument to update
        section_key: Internal section key (e.g., "requirements_functional")
        content: Text content to add
        feature_name: Optional feature name (defaults to first feature or "General")

    Returns:
        Updated AgentOSDocument
    """
    if not content or not content.strip():
        return doc

    content = content.strip()

    # Ensure at least one feature exists
    if not doc.features:
        doc.features.append({
            "name": feature_name or "General",
            "overview": "",
            "requirements_functional": [],
            "requirements_technical": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "technical_spec": {},
            "success_metrics": ""
        })

    # Find the target feature
    target_feature = doc.features[0]
    if feature_name:
        for f in doc.features:
            if f.get("name") == feature_name:
                target_feature = f
                break

    # Add content to appropriate section
    if section_key == "overview":
        if target_feature.get("overview"):
            target_feature["overview"] += "\n\n" + content
        else:
            target_feature["overview"] = content

    elif section_key == "requirements_functional":
        # Split by sentences or bullet points
        items = _split_into_items(content)
        for item in items:
            if item not in target_feature.get("requirements_functional", []):
                target_feature.setdefault("requirements_functional", []).append(item)

    elif section_key == "requirements_technical":
        items = _split_into_items(content)
        for item in items:
            if item not in target_feature.get("requirements_technical", []):
                target_feature.setdefault("requirements_technical", []).append(item)

    elif section_key == "user_stories":
        items = _split_into_items(content)
        for item in items:
            if item not in target_feature.get("user_stories", []):
                target_feature.setdefault("user_stories", []).append(item)

    elif section_key == "acceptance_criteria":
        items = _split_into_items(content)
        for item in items:
            if item not in target_feature.get("acceptance_criteria", []):
                target_feature.setdefault("acceptance_criteria", []).append(item)

    elif section_key == "technical_spec":
        # Try to categorize technical spec content
        tech_spec = target_feature.setdefault("technical_spec", {})
        content_lower = content.lower()

        if "api" in content_lower or "endpoint" in content_lower:
            if tech_spec.get("api_endpoints"):
                tech_spec["api_endpoints"] += "\n" + content
            else:
                tech_spec["api_endpoints"] = content
        elif "model" in content_lower or "data" in content_lower or "database" in content_lower:
            if tech_spec.get("data_models"):
                tech_spec["data_models"] += "\n" + content
            else:
                tech_spec["data_models"] = content
        elif "depend" in content_lower or "library" in content_lower or "package" in content_lower:
            if tech_spec.get("dependencies"):
                tech_spec["dependencies"] += "\n" + content
            else:
                tech_spec["dependencies"] = content
        elif "edge" in content_lower or "error" in content_lower or "exception" in content_lower:
            if tech_spec.get("edge_cases"):
                tech_spec["edge_cases"] += "\n" + content
            else:
                tech_spec["edge_cases"] = content
        else:
            # Default: add to general tech spec
            if tech_spec.get("other"):
                tech_spec["other"] += "\n" + content
            else:
                tech_spec["other"] = content

    elif section_key == "success_metrics":
        if target_feature.get("success_metrics"):
            target_feature["success_metrics"] += "\n\n" + content
        else:
            target_feature["success_metrics"] = content

    elif section_key == "questions":
        items = _split_into_items(content)
        for item in items:
            if item not in doc.questions:
                doc.questions.append(item)

    # Standards layer
    elif section_key == "tech_stack":
        items = _split_into_items(content)
        for item in items:
            if item not in doc.tech_stack:
                doc.tech_stack.append(item)

    elif section_key == "architecture":
        items = _split_into_items(content)
        for item in items:
            if item not in doc.architecture:
                doc.architecture.append(item)

    elif section_key == "coding_patterns":
        items = _split_into_items(content)
        for item in items:
            if item not in doc.coding_patterns:
                doc.coding_patterns.append(item)

    # Product layer
    elif section_key == "vision":
        if doc.vision:
            doc.vision += "\n\n" + content
        else:
            doc.vision = content

    elif section_key == "target_users":
        items = _split_into_items(content)
        for item in items:
            if item not in doc.target_users:
                doc.target_users.append(item)

    elif section_key == "use_cases":
        items = _split_into_items(content)
        for item in items:
            if item not in doc.use_cases:
                doc.use_cases.append(item)

    # Recalculate completion
    doc.calculate_completion()

    ProcessLog.info(
        "AgentOS",
        f"Added voice content to {section_key}",
        details={"chars": len(content), "feature": target_feature.get("name")}
    )

    return doc


def _split_into_items(text: str) -> List[str]:
    """
    Split text into list items.

    Handles various formats:
    - Numbered lists (1. 2. 3.)
    - Bullet points (- * +)
    - Sentences

    Args:
        text: Text to split

    Returns:
        List of individual items
    """
    import re

    # First try to split by common list patterns
    # Numbered: 1. or 1)
    numbered_pattern = r'(?:^|\n)\s*\d+[\.\)]\s*'
    # Bullets: - * +
    bullet_pattern = r'(?:^|\n)\s*[\-\*\+]\s*'

    # Check if text has numbered or bullet format
    if re.search(numbered_pattern, text) or re.search(bullet_pattern, text):
        # Split by patterns
        items = re.split(r'(?:^|\n)\s*(?:\d+[\.\)]|[\-\*\+])\s*', text)
        items = [item.strip() for item in items if item.strip()]
        return items

    # Otherwise try to split by sentences
    # Simple sentence split (not perfect but good enough for voice input)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # If we get just one item or very few, return as-is
    if len(sentences) <= 1:
        return [text.strip()] if text.strip() else []

    return sentences


def generate_agent_os_from_tagged_rant(
    tagged_segments: List[Dict],
    raw_transcript: str,
    openai_api_key: str,
    project_name: Optional[str] = None,
    model: str = "gpt-4-turbo-preview",
    use_ai_classification: bool = True
) -> AgentOSDocument:
    """
    Generate Agent OS document from tagged voice rant.

    Args:
        tagged_segments: List of {section, text, start_time, end_time}
        raw_transcript: Complete unmodified transcript
        openai_api_key: OpenAI API key
        project_name: Optional project name
        model: Model to use for AI classification
        use_ai_classification: Whether to use AI to enhance classification

    Returns:
        Generated AgentOSDocument
    """
    ProcessLog.info("AgentOS", "Generating Agent OS from tagged voice rant")

    # Create base document
    doc = AgentOSDocument(
        name=project_name or "Voice Rant Project",
        raw_rant=raw_transcript
    )

    # Process each tagged segment
    for segment in tagged_segments:
        section_display = segment.get("section", "")
        text = segment.get("text", "")

        if not text:
            continue

        # Map display name to section key
        section_key = VOICE_SECTION_MAP.get(section_display, section_display.lower().replace(" ", "_"))

        # If AI classification is enabled and we have an API key, enhance the content
        if use_ai_classification and openai_api_key:
            # Classify this segment for more precise placement
            items, suggested_name = classify_text(text, openai_api_key, model)

            if items:
                doc = _merge_items_into_document(doc, items)

                # Use suggested name if we don't have one
                if not project_name and suggested_name and suggested_name != "Untitled Project":
                    doc.name = suggested_name
            else:
                # Fall back to direct placement
                doc = add_tagged_content_to_document(doc, section_key, text)
        else:
            # Direct placement without AI enhancement
            doc = add_tagged_content_to_document(doc, section_key, text)

    doc.calculate_completion()

    ProcessLog.success(
        "AgentOS",
        f"Generated Agent OS from tagged rant: {doc.name} ({doc.completion_percentage}% complete)",
        details={"segments": len(tagged_segments), "completion": doc.completion_percentage}
    )

    return doc


def get_organized_view(
    tagged_segments: List[Dict]
) -> Dict[str, str]:
    """
    Get organized content view from tagged segments.

    Groups all text by section.

    Args:
        tagged_segments: List of {section, text, start_time, end_time}

    Returns:
        Dict mapping section name to concatenated text
    """
    organized = {}

    for segment in tagged_segments:
        section = segment.get("section", "Untagged")
        text = segment.get("text", "")

        if section not in organized:
            organized[section] = ""

        organized[section] += text + " "

    # Clean up whitespace
    return {k: v.strip() for k, v in organized.items() if v.strip()}
