"""
Baton service for snapshot generation and warm-up management.

Handles creation of baton snapshots, session warm-up, and auto-baton triggers.
"""

from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from openai import OpenAI
from datetime import datetime

from app.core.models import (
    BatonSnapshot,
    ChatSession,
    ChatMessage,
    MessageRole,
    SessionStatus,
    Project,
    ProjectContext,
    Node,
    NodeVersion,
    NodeStatus,
)
from app.config.settings import settings as app_settings
from app.services.summary_service import get_combined_description


def _gather_project_state(
    db: Session,
    project_id: int
) -> Dict:
    """
    Gather current project state for baton snapshot.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Dictionary containing project state
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get combined project description based on description_mode
    combined_description = get_combined_description(db, project_id)

    # Get all active nodes with current versions
    nodes = db.query(Node).filter(
        Node.project_id == project_id,
        Node.status.in_([NodeStatus.ACTIVE, NodeStatus.DRAFT])
    ).all()

    nodes_data = []
    for node in nodes:
        # Get current version
        current_version = db.query(NodeVersion).filter(
            NodeVersion.node_id == node.id,
            NodeVersion.id == node.current_version_id
        ).first()

        nodes_data.append({
            "id": node.id,
            "name": node.name,
            "type": node.node_type.value,
            "status": node.status.value,
            "description": node.description,
            "content": current_version.content if current_version else None,
        })

    # Get recent node version changes (last 10)
    recent_versions = db.query(NodeVersion).join(Node).filter(
        Node.project_id == project_id
    ).order_by(desc(NodeVersion.created_at)).limit(10).all()

    recent_changes = []
    for version in recent_versions:
        node = db.query(Node).filter(Node.id == version.node_id).first()
        if node:
            recent_changes.append({
                "node_name": node.name,
                "version_number": version.version_number,
                "change_summary": version.change_summary,
                "created_at": version.created_at.isoformat(),
            })

    # Get draft nodes
    drafts = db.query(Node).filter(
        Node.project_id == project_id,
        Node.status == NodeStatus.DRAFT
    ).all()

    drafts_data = []
    for draft in drafts:
        current_version = db.query(NodeVersion).filter(
            NodeVersion.node_id == draft.id,
            NodeVersion.id == draft.current_version_id
        ).first()

        drafts_data.append({
            "name": draft.name,
            "type": draft.node_type.value,
            "description": draft.description,
        })

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        },
        "combined_description": combined_description,
        "nodes": nodes_data,
        "recent_changes": recent_changes,
        "drafts": drafts_data,
        "node_count": len(nodes_data),
        "draft_count": len(drafts_data),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _build_baton_prompt(
    project_state: Dict,
    baton_description_prompt: str
) -> str:
    """
    Build prompt for OpenAI to generate baton description.

    Args:
        project_state: Project state dictionary
        baton_description_prompt: Template from settings

    Returns:
        Formatted prompt string
    """
    # Format project state as readable text
    state_text = f"""# Project: {project_state['project']['name']}

## Project Description
{project_state['project']['description'] or 'No description provided'}

## Project Context
{project_state['combined_description']}

## Current State
- Total Nodes: {project_state['node_count']}
- Draft Nodes: {project_state['draft_count']}

## Active Nodes by Domain
"""

    # Group nodes by domain
    nodes_by_domain = {}
    for node in project_state['nodes']:
        domain = node['domain'] or 'Uncategorized'
        if domain not in nodes_by_domain:
            nodes_by_domain[domain] = []
        nodes_by_domain[domain].append(node)

    for domain, nodes in sorted(nodes_by_domain.items()):
        state_text += f"\n### {domain}\n"
        for node in nodes:
            status_marker = "🟡" if node['status'] == 'draft' else "🟢"
            state_text += f"- {status_marker} **{node['title']}** ({node['type']})\n"
            if node['summary']:
                state_text += f"  - {node['summary']}\n"

    # Add recent changes
    if project_state['recent_changes']:
        state_text += "\n## Recent Changes\n"
        for change in project_state['recent_changes'][:5]:  # Show top 5
            state_text += f"- **{change['node_title']}** v{change['version_number']}: {change['summary']}\n"
            if change['change_note']:
                state_text += f"  - {change['change_note']}\n"

    # Add drafts
    if project_state['drafts']:
        state_text += "\n## Pending Drafts\n"
        for draft in project_state['drafts']:
            state_text += f"- **{draft['title']}** ({draft['domain']})\n"
            if draft['summary']:
                state_text += f"  - {draft['summary']}\n"

    # Use custom prompt template or default
    if baton_description_prompt and baton_description_prompt.strip():
        prompt_template = baton_description_prompt
    else:
        prompt_template = """You are creating a comprehensive snapshot description (a "baton") of the current project state.

Review the project information below and create a well-structured markdown document that:
1. Summarizes the overall project status
2. Highlights key components and their current state
3. Notes any important recent changes or decisions
4. Flags any pending drafts or decisions
5. Provides context for someone picking up this conversation

Be concise but thorough. Use markdown formatting for clarity."""

    # Combine template and state
    full_prompt = f"{prompt_template}\n\n{state_text}"

    return full_prompt


async def _run_warmup_sequence(
    db: Session,
    session: ChatSession,
    warmup_prompts: List[str],
    openai_api_key: str,
    chat_model: str
) -> None:
    """
    Run warm-up sequence for a new session.

    Args:
        db: Database session
        session: Chat session to warm up
        warmup_prompts: List of warm-up prompts
        openai_api_key: OpenAI API key
        chat_model: Model to use
    """
    client = OpenAI(api_key=openai_api_key)

    # Update session status to warming
    session.status = SessionStatus.WARMING
    db.commit()

    # Get all messages so far (should include baton snapshot)
    messages_for_api = []
    existing_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at).all()

    for msg in existing_messages:
        messages_for_api.append({
            "role": msg.role.value,
            "content": msg.content
        })

    # Process each warm-up prompt
    for i, prompt in enumerate(warmup_prompts):
        if not prompt or not prompt.strip():
            continue

        # Add warm-up prompt as user message
        warmup_user_msg = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content=prompt,
            is_warmup=True
        )
        db.add(warmup_user_msg)
        db.commit()
        db.refresh(warmup_user_msg)

        # Add to API messages
        messages_for_api.append({
            "role": "user",
            "content": prompt
        })

        # Get AI response
        try:
            response = client.chat.completions.create(
                model=chat_model,
                messages=messages_for_api,
                temperature=0.7
            )

            assistant_content = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Save assistant response
            warmup_assistant_msg = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                is_warmup=True,
                token_count=completion_tokens,
                model_used=chat_model
            )
            db.add(warmup_assistant_msg)

            # Update session token counts
            session.total_prompt_tokens += prompt_tokens
            session.total_completion_tokens += completion_tokens
            session.total_tokens_used += total_tokens

            db.commit()
            db.refresh(warmup_assistant_msg)

            # Add assistant response to messages
            messages_for_api.append({
                "role": "assistant",
                "content": assistant_content
            })

        except Exception as e:
            # Log error but continue with remaining prompts
            # Silently skip failed warm-up prompts to avoid interrupting the warm-up flow
            continue

    # Mark session as warmed and ready
    session.status = SessionStatus.WARMED_PENDING
    db.commit()


def generate_baton(
    db: Session,
    user_id: int,
    project_id: int,
    from_session_id: int,
    settings: Dict[str, str],
    run_warmup: bool = True
) -> Tuple[BatonSnapshot, ChatSession]:
    """
    Generate a baton snapshot and create a new warmed session.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID
        from_session_id: Source session ID
        settings: Application settings dictionary
        run_warmup: Whether to run warm-up sequence

    Returns:
        Tuple of (BatonSnapshot, new ChatSession)

    Raises:
        Exception: If baton generation fails
    """
    # Gather project state
    project_state = _gather_project_state(db, project_id)

    # Build baton prompt
    baton_prompt_template = settings.get("baton_description_prompt", "")
    baton_prompt = _build_baton_prompt(project_state, baton_prompt_template)

    # Get OpenAI settings
    api_key = settings.get("OPENAI_API_KEY") or app_settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key not configured")

    summary_model = settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")

    # Call OpenAI to generate baton description
    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=summary_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates comprehensive project snapshot descriptions."},
                {"role": "user", "content": baton_prompt}
            ],
            temperature=0.7
        )

        snapshot_body = response.choices[0].message.content

    except Exception as e:
        raise Exception(f"Failed to generate baton description: {str(e)}")

    # Create new chat session
    project = db.query(Project).filter(Project.id == project_id).first()
    new_session = ChatSession(
        user_id=user_id,
        project_id=project_id,
        title=f"Baton Session - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        description=f"Warmed session created from session {from_session_id}",
        session_type="baton",
        is_active=True,
        status=SessionStatus.WARMING if run_warmup else SessionStatus.WARMED_PENDING,
        total_prompt_tokens=0,
        total_completion_tokens=0,
        total_tokens_used=0
    )
    db.add(new_session)
    db.flush()  # Get new_session.id

    # Create baton snapshot
    baton = BatonSnapshot(
        session_id=new_session.id,
        user_id=user_id,
        project_id=project_id,
        snapshot_name=f"Baton {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        description=f"Snapshot from session {from_session_id}",
        snapshot_body=snapshot_body,
        state_data=project_state,
        snapshot_type="manual",  # Will be updated if auto
        created_by=f"user_{user_id}"
    )
    db.add(baton)

    # Add baton snapshot as system message in new session
    baton_message = ChatMessage(
        session_id=new_session.id,
        role=MessageRole.SYSTEM,
        content=f"# Project Snapshot (Baton)\n\n{snapshot_body}",
        is_warmup=False
    )
    db.add(baton_message)

    db.commit()
    db.refresh(baton)
    db.refresh(new_session)

    # Run warm-up if enabled
    if run_warmup:
        auto_warmup = settings.get("auto_warmup_enabled", "true").lower() == "true"

        if auto_warmup:
            # Collect warm-up prompts
            warmup_prompts = []
            for i in range(1, 5):
                prompt = settings.get(f"warmup_prompt_{i}", "")
                if prompt and prompt.strip():
                    warmup_prompts.append(prompt)

            if warmup_prompts:
                # Run warm-up in synchronous context (Streamlit doesn't support async well)
                # We'll call a synchronous version
                _run_warmup_sequence_sync(
                    db,
                    new_session,
                    warmup_prompts,
                    api_key,
                    settings.get("DEFAULT_CHAT_MODEL", "gpt-4-turbo-preview")
                )
            else:
                # No prompts, mark as ready
                new_session.status = SessionStatus.WARMED_PENDING
                db.commit()
        else:
            # Auto warmup disabled, mark as ready
            new_session.status = SessionStatus.WARMED_PENDING
            db.commit()

    return baton, new_session


def _run_warmup_sequence_sync(
    db: Session,
    session: ChatSession,
    warmup_prompts: List[str],
    openai_api_key: str,
    chat_model: str
) -> None:
    """
    Synchronous version of warm-up sequence.

    Args:
        db: Database session
        session: Chat session to warm up
        warmup_prompts: List of warm-up prompts
        openai_api_key: OpenAI API key
        chat_model: Model to use
    """
    client = OpenAI(api_key=openai_api_key)

    # Update session status to warming
    session.status = SessionStatus.WARMING
    db.commit()

    # Get all messages so far (should include baton snapshot)
    messages_for_api = []
    existing_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at).all()

    for msg in existing_messages:
        messages_for_api.append({
            "role": msg.role.value,
            "content": msg.content
        })

    # Process each warm-up prompt
    for i, prompt in enumerate(warmup_prompts):
        if not prompt or not prompt.strip():
            continue

        # Add warm-up prompt as user message
        warmup_user_msg = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content=prompt,
            is_warmup=True
        )
        db.add(warmup_user_msg)
        db.commit()
        db.refresh(warmup_user_msg)

        # Add to API messages
        messages_for_api.append({
            "role": "user",
            "content": prompt
        })

        # Get AI response
        try:
            response = client.chat.completions.create(
                model=chat_model,
                messages=messages_for_api,
                temperature=0.7
            )

            assistant_content = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            # Save assistant response
            warmup_assistant_msg = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                is_warmup=True,
                token_count=completion_tokens,
                model_used=chat_model
            )
            db.add(warmup_assistant_msg)

            # Update session token counts
            session.total_prompt_tokens += prompt_tokens
            session.total_completion_tokens += completion_tokens
            session.total_tokens_used += total_tokens

            db.commit()
            db.refresh(warmup_assistant_msg)

            # Add assistant response to messages
            messages_for_api.append({
                "role": "assistant",
                "content": assistant_content
            })

        except Exception as e:
            # Log error but continue with remaining prompts
            # Silently skip failed warm-up prompts to avoid interrupting the warm-up flow
            continue

    # Mark session as warmed and ready
    session.status = SessionStatus.WARMED_PENDING
    db.commit()


def check_auto_baton_trigger(
    db: Session,
    session_id: int,
    settings: Dict[str, str]
) -> bool:
    """
    Check if auto baton should be triggered for a session.

    Args:
        db: Database session
        session_id: Chat session ID
        settings: Application settings

    Returns:
        True if auto baton should be triggered
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return False

    # Get threshold from settings
    try:
        threshold = int(settings.get("auto_baton_threshold_percent", "80"))
    except ValueError:
        threshold = 80

    max_tokens = int(settings.get("max_context_tokens", "8000"))

    # Calculate percentage used
    percent_used = (session.total_tokens_used / max_tokens) * 100 if max_tokens > 0 else 0

    # Check if we've crossed threshold
    if percent_used >= threshold:
        # Check if we've already created a baton for this session
        # Look for any baton that references this project created recently
        existing_baton = db.query(BatonSnapshot).filter(
            BatonSnapshot.project_id == session.project_id,
            BatonSnapshot.snapshot_type == "auto",
            BatonSnapshot.created_at > session.created_at
        ).first()

        # Trigger if no baton exists yet
        return existing_baton is None

    return False


def get_warmed_sessions(
    db: Session,
    user_id: int,
    project_id: int
) -> List[ChatSession]:
    """
    Get all warmed_pending sessions for a user/project.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        List of warmed pending sessions
    """
    return db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.project_id == project_id,
        ChatSession.status == SessionStatus.WARMED_PENDING,
        ChatSession.is_active == True
    ).order_by(desc(ChatSession.created_at)).all()


def switch_to_session(
    db: Session,
    old_session_id: int,
    new_session_id: int
) -> None:
    """
    Switch from old session to new warmed session.

    Args:
        db: Database session
        old_session_id: Old session ID to deactivate
        new_session_id: New session ID to activate
    """
    # Deactivate old session
    old_session = db.query(ChatSession).filter(ChatSession.id == old_session_id).first()
    if old_session:
        old_session.is_active = False

    # Activate new session and mark as active (not warmed_pending anymore)
    new_session = db.query(ChatSession).filter(ChatSession.id == new_session_id).first()
    if new_session:
        new_session.status = SessionStatus.ACTIVE
        new_session.is_active = True

    db.commit()
