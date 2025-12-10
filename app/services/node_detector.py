"""
Node Detection Service.

Automatically detects potential nodes from chat conversations.
Uses AI to identify components, features, assets, and concepts that should be tracked.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
import json
import time

from app.core.models import NodeType, NodeStatus
from app.services.process_log import ProcessLog


# ============================================================================
# NODE DEFINITION
# ============================================================================
#
# A NODE is a discrete, trackable unit of work or concept in a design project.
#
# Think of nodes as the "building blocks" of your project - anything important
# enough to name, describe, and track separately.
#
# NODE TYPES:
# -----------
# ROOT (🌳)      - Top-level project elements, main features, or primary areas
#                  Examples: "User Authentication System", "Dashboard", "Mobile App"
#
# FOLDER (📁)    - Groupings of related items, categories, or sections
#                  Examples: "Navigation Components", "Form Elements", "API Endpoints"
#
# COMPONENT (🧩) - Specific features, parts, or functional units
#                  Examples: "Login Form", "Search Bar", "User Profile Card"
#
# ASSET (🎨)     - Design elements, visual resources, or media
#                  Examples: "Brand Colors", "Logo Variations", "Hero Image"
#
# NOTE (📝)      - Documentation, decisions, or important information
#                  Examples: "Design Guidelines", "API Decisions", "User Research Notes"
#
# HOW THE DETECTOR WORKS:
# -----------------------
# After each chat exchange, we analyze the conversation for:
# 1. Named features or components ("the login page", "a search function")
# 2. Design elements being discussed ("the color scheme", "button styles")
# 3. Concepts or decisions that should be documented
# 4. Anything the user is describing in detail that deserves its own entry
#
# The AI looks for language patterns that indicate something trackable:
# - "We need a..." / "I want a..."
# - "The [thing] should..."
# - Detailed descriptions of features or elements
# - Design decisions or constraints
# ============================================================================


@dataclass
class DetectedNode:
    """A potential node detected from conversation."""
    suggested_name: str
    suggested_type: NodeType
    suggested_description: str
    confidence: float  # 0.0 to 1.0
    source_text: str  # The text that triggered detection
    reason: str  # Why this was detected as a node


# Detection prompt template
NODE_DETECTION_PROMPT = """You are analyzing a design project conversation to identify potential "nodes" - trackable components, features, or concepts that should be documented.

A NODE is anything important enough to track separately:
- Components (login form, search bar, user profile)
- Features (authentication system, notification service)
- Design elements (color palette, typography, icons)
- Concepts or decisions (navigation flow, data model)
- Assets (hero image, logo, illustrations)

NODE TYPES:
- ROOT: Top-level features or main areas
- FOLDER: Groups of related items
- COMPONENT: Specific parts or features
- ASSET: Design elements or visuals
- NOTE: Documentation or decisions

Analyze this conversation exchange and identify any potential nodes:

USER MESSAGE:
{user_message}

AI RESPONSE:
{assistant_message}

Return a JSON array of detected nodes. For each node include:
- "name": short, clear name (2-5 words)
- "type": one of ROOT, FOLDER, COMPONENT, ASSET, NOTE
- "description": 1-2 sentence description of what this is
- "confidence": 0.0-1.0 how certain this should be a node
- "source_text": the specific text that mentions this
- "reason": brief explanation of why this is node-worthy

Only include items with confidence >= 0.6. Return empty array [] if nothing qualifies.

IMPORTANT:
- Don't create nodes for general conversation or questions
- Focus on specific, nameable things being discussed
- Higher confidence for detailed descriptions or explicit feature requests
- Lower confidence for passing mentions

Return ONLY valid JSON array, no other text."""


def detect_nodes_from_exchange(
    user_message: str,
    assistant_message: str,
    openai_api_key: str,
    model: str = "gpt-4-turbo-preview"
) -> List[DetectedNode]:
    """
    Detect potential nodes from a chat exchange.

    Args:
        user_message: The user's message
        assistant_message: The AI assistant's response
        openai_api_key: OpenAI API key
        model: Model to use for detection

    Returns:
        List of DetectedNode objects
    """
    if not openai_api_key:
        ProcessLog.warning("NodeDetector", "No API key for node detection")
        return []

    # Skip very short exchanges
    if len(user_message) < 20 and len(assistant_message) < 50:
        return []

    prompt = NODE_DETECTION_PROMPT.format(
        user_message=user_message,
        assistant_message=assistant_message
    )

    try:
        ProcessLog.info("NodeDetector", "Analyzing conversation for potential nodes")
        start_time = time.time()

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a JSON-only response bot. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temp for more consistent detection
            max_tokens=1000
        )

        duration_ms = (time.time() - start_time) * 1000
        response_text = response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            nodes_data = json.loads(response_text)

            if not isinstance(nodes_data, list):
                ProcessLog.warning("NodeDetector", "Response was not a list")
                return []

            detected_nodes = []
            for node_data in nodes_data:
                try:
                    # Map type string to NodeType enum
                    type_str = node_data.get("type", "COMPONENT").upper()
                    node_type = NodeType[type_str] if type_str in NodeType.__members__ else NodeType.COMPONENT

                    node = DetectedNode(
                        suggested_name=node_data.get("name", "Unnamed"),
                        suggested_type=node_type,
                        suggested_description=node_data.get("description", ""),
                        confidence=float(node_data.get("confidence", 0.5)),
                        source_text=node_data.get("source_text", ""),
                        reason=node_data.get("reason", "")
                    )

                    # Only include if confidence >= 0.6
                    if node.confidence >= 0.6:
                        detected_nodes.append(node)

                except (KeyError, ValueError) as e:
                    ProcessLog.warning("NodeDetector", f"Skipped invalid node: {e}")
                    continue

            ProcessLog.success(
                "NodeDetector",
                f"Detected {len(detected_nodes)} potential nodes",
                details={"count": len(detected_nodes)},
                duration_ms=duration_ms
            )

            return detected_nodes

        except json.JSONDecodeError as e:
            ProcessLog.error("NodeDetector", f"Failed to parse JSON: {e}", details={"response": response_text[:200]})
            return []

    except Exception as e:
        ProcessLog.error("NodeDetector", f"Detection failed: {str(e)}")
        return []


def get_node_type_icon(node_type: NodeType) -> str:
    """Get emoji icon for node type."""
    icons = {
        NodeType.ROOT: "🌳",
        NodeType.FOLDER: "📁",
        NodeType.COMPONENT: "🧩",
        NodeType.ASSET: "🎨",
        NodeType.NOTE: "📝",
    }
    return icons.get(node_type, "📄")


def format_detected_node_summary(node: DetectedNode) -> str:
    """Format a detected node for display."""
    icon = get_node_type_icon(node.suggested_type)
    confidence_bar = "●" * int(node.confidence * 5) + "○" * (5 - int(node.confidence * 5))

    return f"""
{icon} **{node.suggested_name}** ({node.suggested_type.value})
*{node.suggested_description}*
Confidence: {confidence_bar} ({node.confidence:.0%})
"""


# ============================================================================
# NODE DEFINITION DOCUMENTATION (for users)
# ============================================================================

NODE_DEFINITION_DOC = """
## What is a Node?

A **Node** is any discrete, trackable element in your design project. Think of nodes as the "building blocks" that make up your project - anything important enough to name, describe, and track separately.

### Node Types

| Type | Icon | Use For |
|------|------|---------|
| **Root** | 🌳 | Top-level features, main areas, primary systems |
| **Folder** | 📁 | Groups of related items, categories, sections |
| **Component** | 🧩 | Specific parts, features, UI elements |
| **Asset** | 🎨 | Design elements, visuals, media resources |
| **Note** | 📝 | Documentation, decisions, research notes |

### Examples

**Root nodes:**
- "User Authentication System"
- "Dashboard Module"
- "E-commerce Platform"

**Folder nodes:**
- "Navigation Components"
- "Form Elements"
- "API Endpoints"

**Component nodes:**
- "Login Form"
- "Search Bar"
- "User Profile Card"
- "Shopping Cart Button"

**Asset nodes:**
- "Brand Color Palette"
- "Logo Variations"
- "Product Photography"
- "Icon Set"

**Note nodes:**
- "Design System Guidelines"
- "Architecture Decisions"
- "User Research Findings"

### Auto-Detection

When you chat about your project, the AI watches for things that should become nodes:

- **Feature requests**: "I need a search function..." → Component node
- **Design descriptions**: "The header should have..." → Component/Asset node
- **Decisions**: "We decided to use React..." → Note node
- **Groupings**: "All the form components..." → Folder node

When detected, you'll see a suggestion popup. You can:
- ✅ Accept the node as-is
- ✏️ Edit the name/type/description
- ❌ Dismiss if not needed

Over time, this helps you build a complete map of your project automatically!
"""


def get_node_definition_doc() -> str:
    """Return the node definition documentation."""
    return NODE_DEFINITION_DOC
