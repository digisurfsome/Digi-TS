"""
Summary service for auto-generating project descriptions.

Handles automatic description generation from project nodes and content.
"""

from typing import Optional, Dict
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.models import (
    Project,
    ProjectContext,
    Node,
    NodeVersion,
    NodeStatus,
    DescriptionMode,
)
from app.config.settings import settings as app_settings


def generate_auto_project_description(
    db: Session,
    project_id: int,
    settings: Dict[str, str]
) -> str:
    """
    Generate an automatic project description from all current nodes.

    Args:
        db: Database session
        project_id: Project ID
        settings: Application settings

    Returns:
        Generated auto description text

    Raises:
        Exception: If generation fails
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get project context
    context = db.query(ProjectContext).filter(
        ProjectContext.project_id == project_id,
        ProjectContext.is_active == True
    ).first()

    # Get all active nodes
    nodes = db.query(Node).filter(
        Node.project_id == project_id,
        Node.status.in_([NodeStatus.ACTIVE, NodeStatus.DRAFT])
    ).order_by(Node.node_type, Node.name).all()

    # Build comprehensive project overview
    project_overview = f"""# Project: {project.name}

## Basic Information
- **Project Name**: {project.name}
- **Description**: {project.description or 'No description provided'}
"""

    # Add manual context if available
    if context and context.content:
        project_overview += f"""
## Manual Project Context
{context.content}
"""

    # Group nodes by type
    nodes_by_type = {}
    for node in nodes:
        type_name = node.node_type.value.title() if node.node_type else "Uncategorized"
        if type_name not in nodes_by_type:
            nodes_by_type[type_name] = []
        nodes_by_type[type_name].append(node)

    # Add nodes information
    project_overview += f"""
## Project Structure
Total Components: {len(nodes)}
Types: {len(nodes_by_type)}

### Components by Type
"""

    for type_name, type_nodes in sorted(nodes_by_type.items()):
        project_overview += f"\n#### {type_name} ({len(type_nodes)} components)\n"
        for node in type_nodes:
            # Get current version
            current_version = db.query(NodeVersion).filter(
                NodeVersion.node_id == node.id,
                NodeVersion.id == node.current_version_id
            ).first()

            status_marker = "🟡" if node.status == NodeStatus.DRAFT else "🟢"
            project_overview += f"\n**{status_marker} {node.name}** ({node.node_type.value})\n"

            if node.description:
                project_overview += f"- Description: {node.description}\n"

            if current_version and current_version.content:
                # Include first 200 chars of content
                content_preview = current_version.content[:200].replace('\n', ' ')
                if len(current_version.content) > 200:
                    content_preview += "..."
                project_overview += f"- Content: {content_preview}\n"

    # Get OpenAI settings
    api_key = settings.get("OPENAI_API_KEY") or app_settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key not configured. Please set it in Settings or environment.")

    summary_model = settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")

    # Build prompt for auto description generation
    system_prompt = """You are an AI assistant that creates comprehensive project descriptions.

Given detailed information about a project including its structure, components, and contexts,
create a clear, well-organized project description that:

1. Summarizes the overall purpose and scope of the project
2. Highlights the key domains and their roles
3. Describes the main components and their relationships
4. Captures the current state and maturity level
5. Notes any important patterns, conventions, or design decisions

Format the description in clear, professional markdown. Be concise but thorough.
The description should be 3-5 paragraphs that give someone a complete understanding of the project."""

    user_prompt = f"""Please generate a comprehensive auto-description for this project:

{project_overview}

Create a well-structured description that captures the essence of this project, its structure,
and key components. Focus on what makes this project unique and how the pieces fit together."""

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=summary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        auto_description = response.choices[0].message.content

        # Save to ProjectContext
        if context:
            context.auto_description = auto_description
            db.commit()
            db.refresh(context)
        else:
            # Create new context with auto description
            context = ProjectContext(
                project_id=project_id,
                name="Default Context",
                context_type="general",
                content="",
                auto_description=auto_description,
                description_mode=DescriptionMode.AUTO,
                is_active=True
            )
            db.add(context)
            db.commit()
            db.refresh(context)

        return auto_description

    except Exception as e:
        raise Exception(f"Failed to generate auto description: {str(e)}")


def get_combined_description(
    db: Session,
    project_id: int
) -> str:
    """
    Get the combined project description based on description_mode.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Combined description text based on mode
    """
    context = db.query(ProjectContext).filter(
        ProjectContext.project_id == project_id,
        ProjectContext.is_active == True
    ).first()

    if not context:
        return "No project context available."

    mode = context.description_mode

    if mode == DescriptionMode.MANUAL:
        return context.content or "No manual description provided."

    elif mode == DescriptionMode.AUTO:
        return context.auto_description or "No auto description generated yet."

    elif mode == DescriptionMode.MERGE:
        parts = []

        if context.content:
            parts.append(f"## Manual Description\n\n{context.content}")

        if context.auto_description:
            parts.append(f"## Auto-Generated Description\n\n{context.auto_description}")

        if parts:
            return "\n\n---\n\n".join(parts)
        else:
            return "No descriptions available."

    return "Invalid description mode."


def update_description_mode(
    db: Session,
    project_id: int,
    mode: DescriptionMode
) -> ProjectContext:
    """
    Update the description mode for a project.

    Args:
        db: Database session
        project_id: Project ID
        mode: New description mode

    Returns:
        Updated ProjectContext

    Raises:
        ValueError: If context not found
    """
    context = db.query(ProjectContext).filter(
        ProjectContext.project_id == project_id,
        ProjectContext.is_active == True
    ).first()

    if not context:
        raise ValueError(f"No active context found for project {project_id}")

    context.description_mode = mode
    db.commit()
    db.refresh(context)

    return context
