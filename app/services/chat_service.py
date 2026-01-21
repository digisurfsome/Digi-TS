"""
Chat service for OpenAI integration.

Handles chat sessions, message management, and OpenAI API interactions.
"""

from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from openai import OpenAI
import os
import time

from app.core.models import ChatSession, ChatMessage, MessageRole, Project
from app.core.repositories import BaseRepository
from app.config.settings import settings as app_settings
from app.services.process_log import ProcessLog
from app.services.rag_service import RAGService
from app.services.context_assembler import ContextAssembler


def get_or_create_chat_session(
    db: Session,
    user_id: int,
    project_id: int
) -> ChatSession:
    """
    Get or create default chat session for a project.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        ChatSession
    """
    # Try to get active chat session for this project
    session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.project_id == project_id,
        ChatSession.is_active == True,
        ChatSession.is_archived == False
    ).order_by(ChatSession.created_at.desc()).first()

    if not session:
        # Create new session
        session = ChatSession(
            user_id=user_id,
            project_id=project_id,
            title="Design Chat",
            session_type="general",
            is_active=True,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_tokens_used=0
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    return session


def get_chat_history(db: Session, session_id: int) -> List[ChatMessage]:
    """
    Get chat message history for a session.

    Args:
        db: Database session
        session_id: Chat session ID

    Returns:
        List of ChatMessage objects
    """
    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()


def _build_enhanced_context(
    db: Session,
    project_id: int,
    session_id: int,
    user_text: str,
    max_context_tokens: int = 100000
) -> str:
    """
    Build enhanced context using RAG and Baton systems.

    Args:
        db: Database session
        project_id: Current project ID
        session_id: Current chat session ID
        user_text: The user's current message (used for RAG query)
        max_context_tokens: Maximum tokens for context

    Returns:
        Assembled context string ready for system prompt, or empty string on failure
    """
    try:
        # Initialize services
        rag_service = RAGService(persist_directory="./data/chromadb")
        context_assembler = ContextAssembler(
            db=db,
            rag_service=rag_service,
            max_context_tokens=max_context_tokens
        )

        # Assemble context from Baton + RAG
        assembled_context = context_assembler.assemble(
            current_task=user_text,
            project_id=project_id,
            include_rag=True,
            include_baton=True
        )

        ProcessLog.info("Chat", "Built enhanced context", details={
            "context_length": len(assembled_context) if assembled_context else 0,
            "project_id": project_id
        })

        return assembled_context or ""

    except Exception as e:
        # Fail gracefully - log error but don't break chat
        ProcessLog.warning("Chat", f"Failed to build enhanced context: {str(e)}")
        return ""


def _extract_and_store_to_rag(
    user_text: str,
    assistant_content: str,
    project_id: int,
    session_id: int
) -> None:
    """
    Extract key information from conversation and store in RAG.

    Extracts and stores:
    - Decisions (when assistant confirms a choice or approach)
    - Code changes (when code is written or modified)
    - Errors and solutions (when debugging)
    - Conversation summaries (always, for general retrieval)

    Args:
        user_text: The user's message
        assistant_content: The assistant's response
        project_id: Current project ID
        session_id: Current session ID
    """
    try:
        rag = RAGService(persist_directory="./data/chromadb")

        content_lower = assistant_content.lower()
        stored_items = []

        # Detect and store decisions
        decision_markers = [
            "i'll use", "let's go with", "the best approach",
            "i recommend", "we should", "i've decided",
            "the solution is", "here's the plan", "i suggest"
        ]
        if any(marker in content_lower for marker in decision_markers):
            summary = assistant_content[:500]
            rag.store_decision(
                decision=summary,
                context=user_text[:200],
                tags=["auto-extracted"],
                project_id=project_id,
                session_id=session_id
            )
            stored_items.append("decision")

        # Detect and store code changes
        code_markers = ["```", "def ", "class ", "function ", "const ", "import ", "from "]
        if any(marker in assistant_content for marker in code_markers):
            rag.store_code_change(
                summary=f"Code discussed: {user_text[:100]}",
                files=["auto-detected"],
                details=assistant_content[:1000],
                project_id=project_id,
                session_id=session_id
            )
            stored_items.append("code_change")

        # Detect and store errors/solutions
        error_markers = ["error", "bug", "fix", "issue", "problem", "solution", "traceback", "exception"]
        if any(marker in content_lower for marker in error_markers):
            rag.store_error(
                error=user_text[:300],
                solution=assistant_content[:500],
                project_id=project_id,
                session_id=session_id
            )
            stored_items.append("error_solution")

        # Always store conversation summary
        rag.store_conversation(
            summary=f"Q: {user_text[:150]}... A: {assistant_content[:150]}...",
            key_points=[user_text[:100]],
            project_id=project_id,
            session_id=session_id
        )
        stored_items.append("conversation")

        if stored_items:
            ProcessLog.info("RAG", f"Stored extractions: {', '.join(stored_items)}")

    except Exception as e:
        # Never fail the chat if RAG storage fails
        ProcessLog.warning("RAG", f"Extraction storage failed: {str(e)}")


def send_chat_message(
    db: Session,
    project_id: int,
    session_id: int,
    user_text: str,
    openai_api_key: Optional[str] = None,
    chat_model: str = "gpt-4-turbo-preview",
    settings: Optional[Dict] = None
) -> Tuple[ChatMessage, ChatMessage]:
    """
    Send a chat message and get AI response.

    Args:
        db: Database session
        project_id: Project ID
        session_id: Chat session ID
        user_text: User's message text
        openai_api_key: OpenAI API key (uses env if None)
        chat_model: Model to use for chat
        settings: Optional settings dict for RAG/Baton configuration

    Returns:
        Tuple of (user_message, assistant_message)

    Raises:
        Exception: If OpenAI API call fails
    """
    # Get chat session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if not session:
        raise ValueError(f"Chat session {session_id} not found")

    # Check if approaching token threshold
    if settings:
        from app.services.baton_service import check_auto_baton_trigger
        try:
            should_baton = check_auto_baton_trigger(db, session_id, settings)
            if should_baton:
                ProcessLog.warning("Chat", "Token threshold reached - consider creating a baton")
        except Exception as e:
            ProcessLog.warning("Chat", f"Token check failed: {str(e)}")

    # Create user message
    user_message = ChatMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=user_text
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Build enhanced context with RAG + Baton
    max_tokens = 100000
    if settings:
        try:
            max_tokens = int(settings.get("max_context_tokens", "100000"))
        except (ValueError, TypeError):
            max_tokens = 100000

    enhanced_context = _build_enhanced_context(
        db=db,
        project_id=project_id,
        session_id=session_id,
        user_text=user_text,
        max_context_tokens=max_tokens
    )

    # Build message history for OpenAI
    history = get_chat_history(db, session_id)
    messages = []

    # Add system message with project context if available
    project = db.query(Project).filter(Project.id == project_id).first()
    system_content = ""

    if project:
        system_content = f"You are a helpful AI assistant for the project '{project.name}'."

        # Add active project contexts
        if project.contexts:
            active_contexts = [ctx for ctx in project.contexts if ctx.is_active]
            if active_contexts:
                context_text = "\n\n".join([
                    f"## {ctx.name}\n{ctx.content}"
                    for ctx in active_contexts
                ])
                system_content += f"\n\nHere is the project context:\n\n{context_text}"

        # Append enhanced context from RAG + Baton
        if enhanced_context:
            system_content += f"\n\n## Retrieved Context (from RAG + Baton)\n{enhanced_context}"

    if system_content:
        messages.append({
            "role": "system",
            "content": system_content
        })

    # Add chat history (exclude the user message we just added since we'll add it below)
    for msg in history[:-1]:  # Exclude last message (the one we just added)
        messages.append({
            "role": msg.role.value,
            "content": msg.content
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_text
    })

    # Get API key
    api_key = openai_api_key or app_settings.OPENAI_API_KEY
    if not api_key:
        ProcessLog.error("Chat", "No OpenAI API key configured")
        raise ValueError("OpenAI API key not configured. Please set it in Settings or environment.")

    # Call OpenAI API
    try:
        ProcessLog.info("Chat", f"Sending message to {chat_model}", details={
            "model": chat_model,
            "message_count": len(messages),
            "user_message_length": len(user_text),
            "enhanced_context_length": len(enhanced_context) if enhanced_context else 0,
            "has_enhanced_context": bool(enhanced_context)
        })

        start_time = time.time()
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=chat_model,
            messages=messages,
            temperature=0.7
        )
        duration_ms = (time.time() - start_time) * 1000

        # Extract response
        assistant_content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        ProcessLog.success("Chat", f"Received response from {chat_model}", details={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "response_length": len(assistant_content)
        }, duration_ms=duration_ms)

        # Create assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            token_count=completion_tokens,
            model_used=chat_model
        )
        db.add(assistant_message)

        # Update session token counts
        session.total_prompt_tokens += prompt_tokens
        session.total_completion_tokens += completion_tokens
        session.total_tokens_used += total_tokens

        # Extract and store to RAG for future retrieval
        _extract_and_store_to_rag(
            user_text=user_text,
            assistant_content=assistant_content,
            project_id=project_id,
            session_id=session_id
        )

        db.commit()
        db.refresh(assistant_message)

        return user_message, assistant_message

    except Exception as e:
        ProcessLog.error("Chat", f"OpenAI API error: {str(e)}", details={"error": str(e)})
        db.rollback()
        raise Exception(f"OpenAI API error: {str(e)}")


def clear_chat_history(db: Session, session_id: int) -> None:
    """
    Clear all messages from a chat session.

    Args:
        db: Database session
        session_id: Chat session ID
    """
    db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).delete()

    # Reset token counts
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if session:
        session.total_prompt_tokens = 0
        session.total_completion_tokens = 0
        session.total_tokens_used = 0

    db.commit()


def get_token_usage(db: Session, session_id: int) -> Dict[str, int]:
    """
    Get token usage statistics for a session.

    Args:
        db: Database session
        session_id: Chat session ID

    Returns:
        Dictionary with token counts
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    if not session:
        return {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens_used": 0
        }

    return {
        "total_prompt_tokens": session.total_prompt_tokens,
        "total_completion_tokens": session.total_completion_tokens,
        "total_tokens_used": session.total_tokens_used
    }
