"""
Node service for managing design tree nodes and versions.

Handles node CRUD operations, version management, and status transitions.
"""

from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from openai import OpenAI

from app.core.models import Node, NodeVersion, NodeStatus, NodeType, Project
from app.config.settings import settings as app_settings


def list_project_nodes(
    db: Session,
    project_id: int,
    include_deleted: bool = False
) -> List[Node]:
    """
    List all nodes for a project, optionally excluding deleted.

    Args:
        db: Database session
        project_id: Project ID
        include_deleted: Whether to include deleted nodes

    Returns:
        List of Node objects
    """
    query = db.query(Node).filter(Node.project_id == project_id)

    if not include_deleted:
        query = query.filter(Node.status != NodeStatus.DELETED)

    return query.order_by(Node.domain, Node.title).all()


def get_nodes_by_domain(
    db: Session,
    project_id: int,
    include_deleted: bool = False
) -> Dict[str, List[Node]]:
    """
    Get nodes grouped by domain.

    Args:
        db: Database session
        project_id: Project ID
        include_deleted: Whether to include deleted nodes

    Returns:
        Dictionary mapping domain names to lists of nodes
    """
    nodes = list_project_nodes(db, project_id, include_deleted)

    domains: Dict[str, List[Node]] = {}
    for node in nodes:
        domain = node.domain or "Uncategorized"
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(node)

    return domains


def get_draft_nodes(db: Session, project_id: int) -> List[Node]:
    """
    Get all draft/pending nodes for a project.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        List of Node objects with DRAFT status
    """
    return db.query(Node).filter(
        Node.project_id == project_id,
        Node.status == NodeStatus.DRAFT
    ).order_by(Node.created_at.desc()).all()


def get_node_by_id(db: Session, node_id: int) -> Optional[Node]:
    """
    Get a node by ID.

    Args:
        db: Database session
        node_id: Node ID

    Returns:
        Node object or None
    """
    return db.query(Node).filter(Node.id == node_id).first()


def create_node(
    db: Session,
    project_id: int,
    title: str,
    domain: str,
    node_type: NodeType = NodeType.COMPONENT,
    parent_id: Optional[int] = None,
    status: NodeStatus = NodeStatus.DRAFT,
    initial_content: str = ""
) -> Node:
    """
    Create a new node with initial version.

    Args:
        db: Database session
        project_id: Project ID
        title: Node title
        domain: Domain/category
        node_type: Type of node
        parent_id: Parent node ID (optional)
        status: Initial status
        initial_content: Initial content for first version

    Returns:
        Created Node object
    """
    # Create node
    node = Node(
        project_id=project_id,
        title=title,
        domain=domain,
        node_type=node_type,
        parent_id=parent_id,
        status=status,
        current_version_number=1
    )
    db.add(node)
    db.flush()  # Get node.id

    # Create initial version
    version = NodeVersion(
        node_id=node.id,
        version_number=1,
        summary=f"Initial version of {title}",
        details=initial_content,
        change_note="Initial creation"
    )
    db.add(version)

    db.commit()
    db.refresh(node)

    return node


def create_node_version(
    db: Session,
    node_id: int,
    summary: str,
    details: str,
    change_note: str = ""
) -> NodeVersion:
    """
    Create a new version for an existing node.

    Args:
        db: Database session
        node_id: Node ID
        summary: Version summary
        details: Detailed content
        change_note: Note about what changed

    Returns:
        Created NodeVersion object
    """
    node = get_node_by_id(db, node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    # Get next version number
    max_version = db.query(func.max(NodeVersion.version_number)).filter(
        NodeVersion.node_id == node_id
    ).scalar() or 0

    next_version = max_version + 1

    # Create version
    version = NodeVersion(
        node_id=node_id,
        version_number=next_version,
        summary=summary,
        details=details,
        change_note=change_note
    )
    db.add(version)

    # Update node's current version
    node.current_version_number = next_version

    db.commit()
    db.refresh(version)

    return version


def get_node_versions(db: Session, node_id: int) -> List[NodeVersion]:
    """
    Get all versions for a node.

    Args:
        db: Database session
        node_id: Node ID

    Returns:
        List of NodeVersion objects ordered by version number
    """
    return db.query(NodeVersion).filter(
        NodeVersion.node_id == node_id
    ).order_by(NodeVersion.version_number.desc()).all()


def get_node_current_version(db: Session, node_id: int) -> Optional[NodeVersion]:
    """
    Get the current version for a node.

    Args:
        db: Database session
        node_id: Node ID

    Returns:
        NodeVersion object or None
    """
    node = get_node_by_id(db, node_id)
    if not node:
        return None

    return db.query(NodeVersion).filter(
        NodeVersion.node_id == node_id,
        NodeVersion.version_number == node.current_version_number
    ).first()


def update_node_status(
    db: Session,
    node_id: int,
    new_status: NodeStatus
) -> Node:
    """
    Update a node's status.

    Args:
        db: Database session
        node_id: Node ID
        new_status: New status

    Returns:
        Updated Node object
    """
    node = get_node_by_id(db, node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    node.status = new_status
    db.commit()
    db.refresh(node)

    return node


def update_node_basic_info(
    db: Session,
    node_id: int,
    title: Optional[str] = None,
    domain: Optional[str] = None
) -> Node:
    """
    Update node's basic information.

    Args:
        db: Database session
        node_id: Node ID
        title: New title (optional)
        domain: New domain (optional)

    Returns:
        Updated Node object
    """
    node = get_node_by_id(db, node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    if title is not None:
        node.title = title
    if domain is not None:
        node.domain = domain

    db.commit()
    db.refresh(node)

    return node


def delete_node(db: Session, node_id: int, hard_delete: bool = False) -> None:
    """
    Delete a node (soft or hard delete).

    Args:
        db: Database session
        node_id: Node ID
        hard_delete: If True, permanently delete; if False, mark as DELETED
    """
    node = get_node_by_id(db, node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")

    if hard_delete:
        # Delete all versions first
        db.query(NodeVersion).filter(NodeVersion.node_id == node_id).delete()
        # Delete node
        db.delete(node)
    else:
        # Soft delete
        node.status = NodeStatus.DELETED

    db.commit()


def commit_draft_node(db: Session, node_id: int) -> Node:
    """
    Commit a draft node to active status.

    Args:
        db: Database session
        node_id: Node ID

    Returns:
        Updated Node object
    """
    return update_node_status(db, node_id, NodeStatus.ACTIVE)


def summarize_rant(
    rant_text: str,
    openai_api_key: Optional[str] = None,
    summary_model: str = "gpt-4-turbo-preview"
) -> Tuple[str, str]:
    """
    Use OpenAI to summarize a rant into structured markdown.

    Args:
        rant_text: Raw rant text
        openai_api_key: OpenAI API key (uses env if None)
        summary_model: Model to use for summarization

    Returns:
        Tuple of (summary, details) as structured markdown

    Raises:
        Exception: If OpenAI API call fails
    """
    # Get API key
    api_key = openai_api_key or app_settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key not configured. Please set it in Settings or environment.")

    # Create prompt
    system_prompt = """You are an AI assistant that helps organize design thoughts into structured documentation.

Given a raw "rant" or stream-of-consciousness design notes, extract:
1. A concise summary (1-2 sentences)
2. Detailed structured content in markdown format

Format your response exactly as:
SUMMARY:
[Your 1-2 sentence summary]

DETAILS:
[Structured markdown with headers, bullets, etc.]"""

    user_prompt = f"""Please organize this design rant into structured documentation:

{rant_text}"""

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

        # Parse response
        content = response.choices[0].message.content

        # Split into summary and details
        if "SUMMARY:" in content and "DETAILS:" in content:
            parts = content.split("DETAILS:")
            summary_part = parts[0].replace("SUMMARY:", "").strip()
            details_part = parts[1].strip()
        else:
            # Fallback: use first paragraph as summary, rest as details
            lines = content.strip().split("\n\n")
            summary_part = lines[0] if lines else "Summary not available"
            details_part = "\n\n".join(lines[1:]) if len(lines) > 1 else content

        return summary_part, details_part

    except Exception as e:
        raise Exception(f"OpenAI API error during summarization: {str(e)}")


def attach_summary_to_node(
    db: Session,
    node_id: int,
    summary: str,
    details: str,
    change_note: str = "Added from rant summary"
) -> NodeVersion:
    """
    Attach a summary to an existing node as a new version.

    Args:
        db: Database session
        node_id: Node ID
        summary: Summary text
        details: Detailed content
        change_note: Change note

    Returns:
        Created NodeVersion object
    """
    return create_node_version(db, node_id, summary, details, change_note)


def create_node_from_summary(
    db: Session,
    project_id: int,
    title: str,
    domain: str,
    summary: str,
    details: str,
    node_type: NodeType = NodeType.COMPONENT,
    status: NodeStatus = NodeStatus.DRAFT
) -> Node:
    """
    Create a new node from a rant summary.

    Args:
        db: Database session
        project_id: Project ID
        title: Node title
        domain: Domain/category
        summary: Summary text
        details: Detailed content
        node_type: Type of node
        status: Initial status

    Returns:
        Created Node object
    """
    # Create node
    node = Node(
        project_id=project_id,
        title=title,
        domain=domain,
        node_type=node_type,
        status=status,
        current_version_number=1
    )
    db.add(node)
    db.flush()

    # Create initial version with summary
    version = NodeVersion(
        node_id=node.id,
        version_number=1,
        summary=summary,
        details=details,
        change_note="Created from rant summary"
    )
    db.add(version)

    db.commit()
    db.refresh(node)

    return node
