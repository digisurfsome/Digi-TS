"""
Truth Doc export service.

Generates comprehensive markdown documentation of the entire project.
"""

from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.models import (
    Project,
    ProjectContext,
    Node,
    NodeVersion,
    NodeStatus,
    NodeType,
)
from app.services.summary_service import get_combined_description


def export_truth_doc(
    db: Session,
    project_id: int,
    include_archived: bool = False
) -> str:
    """
    Export comprehensive Truth Doc for a project.

    Args:
        db: Database session
        project_id: Project ID
        include_archived: Whether to include archived nodes

    Returns:
        Markdown string of complete project documentation

    Raises:
        ValueError: If project not found
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get combined description based on mode
    description = get_combined_description(db, project_id)

    # Build Truth Doc header
    doc = f"""# {project.name} - Truth Doc

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Project Overview

{description}

---

## Project Details

- **Created**: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Last Updated**: {project.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
- **Project ID**: {project.id}

---

"""

    # Get all nodes
    query = db.query(Node).filter(Node.project_id == project_id)

    if not include_archived:
        query = query.filter(Node.status != NodeStatus.DELETED)

    nodes = query.order_by(Node.node_type, Node.name).all()

    if not nodes:
        doc += "## Components\n\n*No components in this project yet.*\n\n"
        return doc

    # Group nodes by type
    nodes_by_type = {}
    for node in nodes:
        type_name = node.node_type.value.title() if node.node_type else "Uncategorized"
        if type_name not in nodes_by_type:
            nodes_by_type[type_name] = []
        nodes_by_type[type_name].append(node)

    # Add component index
    doc += "## Component Index\n\n"
    doc += f"**Total Components**: {len(nodes)}\n\n"

    for type_name in sorted(nodes_by_type.keys()):
        type_nodes = nodes_by_type[type_name]
        doc += f"### {type_name} ({len(type_nodes)})\n\n"

        for node in type_nodes:
            status_badge = _get_status_badge(node.status)
            type_icon = _get_type_icon(node.node_type)
            doc += f"- {type_icon} **{node.name}** {status_badge}\n"

        doc += "\n"

    doc += "---\n\n"

    # Add detailed component sections
    doc += "## Components\n\n"

    for type_name in sorted(nodes_by_type.keys()):
        type_nodes = nodes_by_type[type_name]

        doc += f"## Type: {type_name}\n\n"

        for node in type_nodes:
            doc += _generate_node_section(db, node)
            doc += "\n"

    # Add footer
    doc += f"""---

## Document Information

This Truth Doc was automatically generated from Design Tree Studio.

- **Project**: {project.name}
- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Components**: {len(nodes)}
- **Types**: {len(nodes_by_type)}

---

*End of Truth Doc*
"""

    return doc


def _generate_node_section(db: Session, node: Node) -> str:
    """
    Generate detailed section for a single node.

    Args:
        db: Database session
        node: Node to document

    Returns:
        Markdown section for the node
    """
    status_badge = _get_status_badge(node.status)
    type_icon = _get_type_icon(node.node_type)

    section = f"### {type_icon} {node.name} {status_badge}\n\n"

    # Node metadata
    section += f"**Type**: {node.node_type.value.title()}\n\n"
    section += f"**Status**: {node.status.value.title()}\n\n"

    if node.description:
        section += f"**Description**: {node.description}\n\n"

    # Get all versions ordered by version number descending
    versions = db.query(NodeVersion).filter(
        NodeVersion.node_id == node.id
    ).order_by(NodeVersion.version_number.desc()).all()

    if not versions:
        section += "*No versions available*\n\n"
        return section

    # Current version (detailed)
    current_version = None
    for v in versions:
        if v.id == node.current_version_id:
            current_version = v
            break

    # If no current version ID set, use the latest
    if not current_version and versions:
        current_version = versions[0]

    if current_version:
        section += f"#### Current Version: v{current_version.version_number}\n\n"

        if current_version.change_summary:
            section += f"**Summary**: {current_version.change_summary}\n\n"

        if current_version.content:
            section += f"**Content**:\n\n{current_version.content}\n\n"

        section += f"*Last Updated*: {current_version.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

    # Version history
    if len(versions) > 1:
        section += "#### Version History\n\n"

        for version in versions:
            if current_version and version.id == current_version.id:
                continue  # Skip current version, already shown

            section += f"**v{version.version_number}** - {version.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

            if version.change_summary:
                section += f"- Summary: {version.change_summary}\n"

            if version.content:
                # Show abbreviated content for older versions
                content_preview = version.content[:150].replace('\n', ' ')
                if len(version.content) > 150:
                    content_preview += "..."
                section += f"- Content: {content_preview}\n"

            section += "\n"

    section += "---\n\n"

    return section


def _get_status_badge(status: NodeStatus) -> str:
    """Get badge for node status."""
    badges = {
        NodeStatus.ACTIVE: "🟢 Active",
        NodeStatus.DRAFT: "🟡 Draft",
        NodeStatus.ARCHIVED: "🔵 Archived",
        NodeStatus.DELETED: "🔴 Deleted",
    }
    return badges.get(status, "⚪ Unknown")


def _get_type_icon(node_type: NodeType) -> str:
    """Get icon for node type."""
    icons = {
        NodeType.ROOT: "🌳",
        NodeType.FOLDER: "📁",
        NodeType.COMPONENT: "🧩",
        NodeType.ASSET: "🎨",
        NodeType.NOTE: "📝",
    }
    return icons.get(node_type, "📄")


def get_truth_doc_filename(project_name: str) -> str:
    """
    Generate filename for Truth Doc export.

    Args:
        project_name: Name of the project

    Returns:
        Sanitized filename
    """
    # Sanitize project name for filename
    safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_'))
    safe_name = safe_name.replace(' ', '_')

    # Add timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    return f"{safe_name}_TruthDoc_{timestamp}.md"


def get_truth_doc_preview(doc: str, max_lines: int = 50) -> str:
    """
    Get preview of Truth Doc (first N lines).

    Args:
        doc: Full Truth Doc markdown
        max_lines: Maximum lines to show

    Returns:
        Preview string
    """
    lines = doc.split('\n')

    if len(lines) <= max_lines:
        return doc

    preview_lines = lines[:max_lines]
    preview = '\n'.join(preview_lines)
    preview += f"\n\n... ({len(lines) - max_lines} more lines) ..."

    return preview
