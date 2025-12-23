"""
Context Assembler Service for the Memory System.

Combines Baton (hot memory) + RAG (long memory) + Current conversation
into an optimal context window for AI interactions.
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import BatonSnapshot


class ContextAssembler:
    """
    Assembles context from multiple sources into a single coherent prompt.
    Manages token budgets to fit within model limits.
    """

    # Token budget allocation (percentages of available context)
    BUDGET = {
        "baton": 0.15,      # 15% for current state (hot memory)
        "rag": 0.25,        # 25% for relevant history (long memory)
        "current": 0.60,    # 60% for current conversation
    }

    def __init__(
        self,
        db: Session,
        rag_service=None,
        max_context_tokens: int = 100000
    ):
        """
        Initialize Context Assembler.

        Args:
            db: Database session for baton queries
            rag_service: The RAG service instance (optional, can be set later)
            max_context_tokens: Maximum tokens for context (model dependent)
        """
        self.db = db
        self.rag = rag_service
        self.max_tokens = max_context_tokens

    def set_rag_service(self, rag_service):
        """Set or update the RAG service instance."""
        self.rag = rag_service

    def load_baton(self, baton_id: int) -> str:
        """
        Load a baton as injectable context string.

        Args:
            baton_id: The baton snapshot ID

        Returns:
            Formatted markdown string ready for context injection
        """
        baton = self.db.query(BatonSnapshot).filter(BatonSnapshot.id == baton_id).first()
        if not baton:
            return ""

        # Use the enhanced fields if available, otherwise fall back to snapshot_body
        sections = []

        sections.append("# Session Baton (Handoff Context)")
        sections.append("")

        # Try enhanced fields first
        state_data = baton.state_data or {}

        if state_data.get("current_state"):
            sections.append("## Current State")
            sections.append(state_data["current_state"])
            sections.append("")

        if state_data.get("completed_items"):
            sections.append("## Completed This Session")
            sections.append(state_data["completed_items"])
            sections.append("")

        if state_data.get("pending_items"):
            sections.append("## Pending Items")
            sections.append(state_data["pending_items"])
            sections.append("")

        if state_data.get("active_context"):
            sections.append("## Active Context")
            sections.append(state_data["active_context"])
            sections.append("")

        if state_data.get("next_steps"):
            sections.append("## Next Steps")
            sections.append(state_data["next_steps"])
            sections.append("")

        if state_data.get("blockers"):
            sections.append("## Blockers")
            sections.append(state_data["blockers"])
            sections.append("")

        # If no enhanced fields, use the full snapshot_body
        if len(sections) <= 2 and baton.snapshot_body:
            sections.append("## Session Summary")
            sections.append(baton.snapshot_body)
            sections.append("")

        sections.append("---")
        sections.append(f"*Baton generated: {baton.created_at}*")

        return "\n".join(sections)

    def get_latest_baton(self, project_id: int = None) -> Optional[BatonSnapshot]:
        """Get the most recent baton, optionally filtered by project."""
        query = self.db.query(BatonSnapshot)
        if project_id:
            query = query.filter(BatonSnapshot.project_id == project_id)
        return query.order_by(desc(BatonSnapshot.created_at)).first()

    def assemble(
        self,
        current_task: str,
        current_conversation: List[Dict] = None,
        baton_id: int = None,
        project_id: int = None,
        include_rag: bool = True,
        include_baton: bool = True
    ) -> str:
        """
        Assemble full context from all sources.

        Args:
            current_task: What we're working on (used for RAG query)
            current_conversation: Recent messages (for reference, not included in output)
            baton_id: Specific baton to load (or uses latest)
            project_id: Project filter for baton
            include_rag: Whether to include RAG context
            include_baton: Whether to include Baton context

        Returns:
            Assembled context string ready for injection
        """
        context_parts = []

        # 1. Load Baton (current state / hot memory)
        if include_baton:
            if baton_id:
                baton_content = self.load_baton(baton_id)
            else:
                latest = self.get_latest_baton(project_id)
                baton_content = self.load_baton(latest.id) if latest else ""

            if baton_content:
                baton_tokens = self._count_tokens(baton_content)
                budget = int(self.max_tokens * self.BUDGET["baton"])

                if baton_tokens > budget:
                    baton_content = self._truncate(baton_content, budget)

                context_parts.append(baton_content)

        # 2. Retrieve RAG context (relevant history / long memory)
        if include_rag and current_task and self.rag:
            rag_content = self.rag.get_relevant_context(
                current_task,
                project_id=project_id
            )

            if rag_content:
                rag_tokens = self._count_tokens(rag_content)
                budget = int(self.max_tokens * self.BUDGET["rag"])

                if rag_tokens > budget:
                    rag_content = self._truncate(rag_content, budget)

                context_parts.append(rag_content)

        # 3. Current conversation (handled by caller, we just leave room for it)
        # This is not included in the assembled context - the caller manages it

        # Combine all parts
        if context_parts:
            assembled = "\n\n---\n\n".join(context_parts)
        else:
            assembled = ""

        return assembled

    def get_context_health(self, current_tokens: int) -> Dict:
        """
        Get health status of context usage.

        Args:
            current_tokens: How many tokens are currently used

        Returns:
            Dict with health metrics
        """
        percentage = (current_tokens / self.max_tokens) * 100 if self.max_tokens > 0 else 0

        if percentage < 50:
            status = "healthy"
            color = "green"
        elif percentage < 75:
            status = "caution"
            color = "yellow"
        else:
            status = "critical"
            color = "red"

        return {
            "current_tokens": current_tokens,
            "max_tokens": self.max_tokens,
            "percentage": round(percentage, 1),
            "status": status,
            "color": color,
            "remaining": self.max_tokens - current_tokens,
            "should_baton": percentage > 70,
            "recommendation": self._get_recommendation(percentage)
        }

    def _get_recommendation(self, percentage: float) -> str:
        """Get recommendation based on context usage."""
        if percentage < 50:
            return "Context healthy. Continue working."
        elif percentage < 70:
            return "Consider creating a checkpoint soon."
        elif percentage < 85:
            return "Create baton now. Context getting full."
        else:
            return "CRITICAL: Generate baton immediately before context overflow."

    def _count_tokens(self, text: str) -> int:
        """Rough token count estimate (4 chars per token average)."""
        return len(text) // 4

    def _truncate(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit token budget."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[... truncated for context budget ...]"

    def get_budget_allocation(self) -> Dict:
        """Get the current budget allocation settings."""
        return {
            "baton_percentage": int(self.BUDGET["baton"] * 100),
            "rag_percentage": int(self.BUDGET["rag"] * 100),
            "current_percentage": int(self.BUDGET["current"] * 100),
            "baton_tokens": int(self.max_tokens * self.BUDGET["baton"]),
            "rag_tokens": int(self.max_tokens * self.BUDGET["rag"]),
            "current_tokens": int(self.max_tokens * self.BUDGET["current"]),
            "max_tokens": self.max_tokens
        }


class EnhancedBatonService:
    """
    Enhanced Baton Service with Memory System integration.

    Manages hot memory - current state and context.
    Works with Context Assembler for optimal context management.
    """

    def __init__(self, db: Session, rag_service=None):
        """
        Initialize Enhanced Baton Service.

        Args:
            db: Database session
            rag_service: Optional RAG service for auto-storing decisions
        """
        self.db = db
        self.rag = rag_service

    def generate_baton(
        self,
        session_id: int = None,
        project_id: int = None,
        user_id: int = None,
        conversation_history: List[Dict] = None,
        custom_sections: Dict = None
    ) -> BatonSnapshot:
        """
        Generate a baton snapshot from current state.

        Args:
            session_id: Optional roundtable session to capture
            project_id: Project ID
            user_id: User ID
            conversation_history: Recent messages to summarize
            custom_sections: Additional sections to include
                - current_state: What we're working on RIGHT NOW
                - completed_items: What's done this session
                - pending_items: What's left to do
                - active_context: Recent decisions/discussion
                - next_steps: Immediate next actions
                - blockers: Current issues

        Returns:
            BatonSnapshot with compressed context
        """
        # Build state_data from custom sections
        state_data = {}

        if custom_sections:
            for key in ["current_state", "completed_items", "pending_items",
                        "active_context", "next_steps", "blockers"]:
                if key in custom_sections:
                    state_data[key] = custom_sections[key]

        # Auto-extract from conversation if provided
        if conversation_history and not custom_sections:
            state_data["current_state"] = self._extract_current_state(conversation_history)
            state_data["completed_items"] = self._extract_completed(conversation_history)
            state_data["pending_items"] = self._extract_pending(conversation_history)
            state_data["next_steps"] = self._extract_next_steps(conversation_history)

        # Build snapshot body from state_data
        snapshot_body = self._build_snapshot_body(state_data)

        # Calculate token count
        token_count = len(snapshot_body) // 4

        # Create baton
        from datetime import datetime
        baton = BatonSnapshot(
            session_id=session_id or 0,
            project_id=project_id or 0,
            user_id=user_id or 0,
            snapshot_name=f"Baton {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            description="Memory System baton snapshot",
            snapshot_body=snapshot_body,
            state_data=state_data,
            snapshot_type="memory_system"
        )

        self.db.add(baton)
        self.db.commit()
        self.db.refresh(baton)

        return baton

    def _build_snapshot_body(self, state_data: Dict) -> str:
        """Build markdown snapshot body from state data."""
        sections = []

        if state_data.get("current_state"):
            sections.append(f"## Current State\n{state_data['current_state']}")

        if state_data.get("completed_items"):
            sections.append(f"## Completed\n{state_data['completed_items']}")

        if state_data.get("pending_items"):
            sections.append(f"## Pending\n{state_data['pending_items']}")

        if state_data.get("active_context"):
            sections.append(f"## Context\n{state_data['active_context']}")

        if state_data.get("next_steps"):
            sections.append(f"## Next Steps\n{state_data['next_steps']}")

        if state_data.get("blockers"):
            sections.append(f"## Blockers\n{state_data['blockers']}")

        return "\n\n".join(sections) if sections else "No state data captured."

    def _extract_current_state(self, history: List[Dict]) -> str:
        """Extract current state from conversation history."""
        if not history:
            return "No conversation history"

        # Get last few messages for context
        recent = history[-3:] if len(history) >= 3 else history
        summary = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            summary.append(f"[{role}]: {content}...")

        return "\n".join(summary)

    def _extract_completed(self, history: List[Dict]) -> str:
        """Extract completed items from conversation."""
        # Simple extraction - look for completion markers
        completed = []
        for msg in history:
            content = msg.get("content", "").lower()
            if any(word in content for word in ["completed", "done", "finished", "✓", "✅"]):
                completed.append(f"- {msg.get('content', '')[:100]}")

        return "\n".join(completed[:5]) if completed else "No completed items detected"

    def _extract_pending(self, history: List[Dict]) -> str:
        """Extract pending items from conversation."""
        # Simple extraction - look for pending markers
        pending = []
        for msg in history:
            content = msg.get("content", "").lower()
            if any(word in content for word in ["todo", "pending", "need to", "should", "will"]):
                pending.append(f"- {msg.get('content', '')[:100]}")

        return "\n".join(pending[:5]) if pending else "No pending items detected"

    def _extract_next_steps(self, history: List[Dict]) -> str:
        """Extract next steps from conversation."""
        if not history:
            return "No next steps identified"

        # Look at last assistant message for next steps
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if "next" in content.lower() or "step" in content.lower():
                    return content[:300]

        return "Continue with current task"

    def load_baton(self, baton_id: int) -> str:
        """
        Load a baton as injectable context string.

        Args:
            baton_id: The baton ID to load

        Returns:
            Formatted markdown string ready for context injection
        """
        baton = self.db.query(BatonSnapshot).filter(BatonSnapshot.id == baton_id).first()
        if not baton:
            return ""

        return f"""# Session Baton (Handoff Context)

## Current State
{baton.state_data.get('current_state', 'No current state recorded') if baton.state_data else 'No state data'}

## Completed This Session
{baton.state_data.get('completed_items', 'Nothing completed yet') if baton.state_data else 'N/A'}

## Pending Items
{baton.state_data.get('pending_items', 'No pending items') if baton.state_data else 'N/A'}

## Active Context
{baton.state_data.get('active_context', 'No active context') if baton.state_data else 'N/A'}

## Next Steps
{baton.state_data.get('next_steps', 'No next steps defined') if baton.state_data else 'N/A'}

## Blockers
{baton.state_data.get('blockers', 'No blockers') if baton.state_data else 'N/A'}

---
*Baton generated: {baton.created_at}*
"""

    def get_latest_baton(self, project_id: int = None) -> Optional[BatonSnapshot]:
        """Get the most recent baton, optionally filtered by project."""
        query = self.db.query(BatonSnapshot)
        if project_id:
            query = query.filter(BatonSnapshot.project_id == project_id)
        return query.order_by(desc(BatonSnapshot.created_at)).first()
