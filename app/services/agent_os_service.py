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
        """Calculate document completion percentage."""
        total_sections = 10
        filled = 0

        if self.tech_stack:
            filled += 1
        if self.architecture:
            filled += 1
        if self.coding_patterns:
            filled += 1
        if self.vision:
            filled += 1
        if self.target_users:
            filled += 1
        if self.use_cases:
            filled += 1
        if any(self.roadmap.values()):
            filled += 1
        if self.features:
            filled += 2  # Features count more
        if self.questions:
            filled += 1

        self.completion_percentage = int((filled / total_sections) * 100)
        return self.completion_percentage

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
