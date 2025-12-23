# Memory System Specification

**Version:** 1.0
**Priority:** CRITICAL - Build this FIRST
**Purpose:** Enable infinite context through Baton + RAG integration

---

## Overview

The Memory System combines two complementary approaches:
- **Baton**: Hot memory - current state, active task, momentum
- **RAG**: Long memory - all decisions, history, searchable

Together they provide effectively infinite context across sessions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MEMORY SYSTEM                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │       BATON         │         │        RAG          │           │
│  │    (Hot Memory)     │         │   (Long Memory)     │           │
│  │                     │         │                     │           │
│  │  • Current state    │         │  • Vector DB        │           │
│  │  • Active task      │         │  • All decisions    │           │
│  │  • Recent context   │         │  • Code changes     │           │
│  │  • Next steps       │         │  • Conversations    │           │
│  │                     │         │  • Searchable       │           │
│  │  Updates: Frequent  │         │  Updates: Every msg │           │
│  │  Size: ~5-10k tok   │         │  Size: Unlimited    │           │
│  └──────────┬──────────┘         └──────────┬──────────┘           │
│             │                               │                       │
│             └───────────────┬───────────────┘                       │
│                             │                                       │
│                             ▼                                       │
│                  ┌─────────────────────┐                           │
│                  │  CONTEXT ASSEMBLER  │                           │
│                  │                     │                           │
│                  │  Combines:          │                           │
│                  │  • Baton (15%)      │                           │
│                  │  • RAG hits (25%)   │                           │
│                  │  • Current (60%)    │                           │
│                  └──────────┬──────────┘                           │
│                             │                                       │
│                             ▼                                       │
│                    [CONTEXT WINDOW]                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Enhanced Baton Service

### Location
`app/services/baton_service.py` (enhance existing)

### Data Model

```python
class BatonSnapshot(Base):
    __tablename__ = "baton_snapshots"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("roundtable_sessions.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Content
    current_state = Column(Text)        # What we're working on RIGHT NOW
    completed_items = Column(Text)      # What's done this session
    pending_items = Column(Text)        # What's left to do
    active_context = Column(Text)       # Recent decisions/discussion
    next_steps = Column(Text)           # Immediate next actions
    blockers = Column(Text)             # Current issues

    # Metadata
    token_count = Column(Integer)       # Size of this baton
    context_percentage = Column(Float)  # How full was context when created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Linking
    parent_baton_id = Column(Integer, ForeignKey("baton_snapshots.id"), nullable=True)
```

### Key Methods

```python
class EnhancedBatonService:
    """
    Manages hot memory - current state and context.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_baton(
        self,
        session_id: int = None,
        conversation_history: List[dict] = None,
        custom_sections: dict = None
    ) -> BatonSnapshot:
        """
        Generate a baton snapshot from current state.

        Args:
            session_id: Optional roundtable session to capture
            conversation_history: Recent messages to summarize
            custom_sections: Additional sections to include

        Returns:
            BatonSnapshot with compressed context
        """
        baton = BatonSnapshot()

        # Auto-generate sections
        if conversation_history:
            baton.current_state = self._extract_current_state(conversation_history)
            baton.completed_items = self._extract_completed(conversation_history)
            baton.pending_items = self._extract_pending(conversation_history)
            baton.next_steps = self._extract_next_steps(conversation_history)

        # Add roundtable context if provided
        if session_id:
            rt_context = self._get_roundtable_context(session_id)
            baton.active_context = rt_context

        # Merge custom sections
        if custom_sections:
            for key, value in custom_sections.items():
                if hasattr(baton, key):
                    setattr(baton, key, value)

        # Calculate token count
        baton.token_count = self._count_tokens(baton)

        self.db.add(baton)
        self.db.commit()
        return baton

    def load_baton(self, baton_id: int) -> str:
        """
        Load a baton as injectable context string.

        Returns:
            Formatted markdown string ready for context injection
        """
        baton = self.db.query(BatonSnapshot).get(baton_id)
        if not baton:
            return ""

        return f"""# Session Baton (Handoff Context)

## Current State
{baton.current_state or "No current state recorded"}

## Completed This Session
{baton.completed_items or "Nothing completed yet"}

## Pending Items
{baton.pending_items or "No pending items"}

## Active Context
{baton.active_context or "No active context"}

## Next Steps
{baton.next_steps or "No next steps defined"}

## Blockers
{baton.blockers or "No blockers"}

---
*Baton generated: {baton.created_at}*
"""

    def get_latest_baton(self, project_id: int = None) -> BatonSnapshot:
        """Get the most recent baton, optionally filtered by project."""
        query = self.db.query(BatonSnapshot)
        if project_id:
            query = query.filter(BatonSnapshot.project_id == project_id)
        return query.order_by(desc(BatonSnapshot.created_at)).first()

    def _extract_current_state(self, history: List[dict]) -> str:
        """Use LLM to extract current state from conversation."""
        # Implementation: Call cheap model to summarize
        pass

    def _count_tokens(self, baton: BatonSnapshot) -> int:
        """Estimate token count of baton content."""
        content = f"{baton.current_state}{baton.completed_items}{baton.pending_items}"
        return len(content) // 4  # Rough estimate
```

---

## Component 2: RAG Service

### Location
`app/services/rag_service.py` (new file)

### Dependencies

```
# Add to requirements.txt
chromadb>=0.4.0
sentence-transformers>=2.2.0  # For embeddings (or use OpenAI)
```

### Data Categories

Store these types of information:

| Category | What | When to Store |
|----------|------|---------------|
| `decisions` | Architectural choices, approach selections | After consensus reached |
| `code_changes` | What was built, file paths, summaries | After code accepted |
| `conversations` | Key discussion points | End of each round |
| `errors` | What went wrong and how it was fixed | After bug fixes |
| `specs` | Requirements, constraints | When defined |

### Implementation

```python
# app/services/rag_service.py

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

class RAGService:
    """
    Long-term memory using vector database.
    Stores and retrieves relevant context from all sessions.
    """

    def __init__(self, persist_directory: str = "./data/chromadb"):
        """
        Initialize RAG service with ChromaDB.

        Args:
            persist_directory: Where to store the vector database
        """
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))

        # Create collections for different content types
        self.collections = {
            "decisions": self.client.get_or_create_collection("decisions"),
            "code_changes": self.client.get_or_create_collection("code_changes"),
            "conversations": self.client.get_or_create_collection("conversations"),
            "errors": self.client.get_or_create_collection("errors"),
            "specs": self.client.get_or_create_collection("specs"),
        }

    def store(
        self,
        content: str,
        category: str,
        metadata: Dict = None,
        session_id: int = None
    ) -> str:
        """
        Store content in the appropriate collection.

        Args:
            content: The text to store
            category: One of: decisions, code_changes, conversations, errors, specs
            metadata: Additional metadata (tags, source, etc.)
            session_id: Optional session ID for filtering

        Returns:
            The document ID
        """
        if category not in self.collections:
            raise ValueError(f"Unknown category: {category}")

        collection = self.collections[category]

        # Generate unique ID
        doc_id = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()[:12]

        # Build metadata
        meta = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
        }
        if session_id:
            meta["session_id"] = str(session_id)
        if metadata:
            meta.update(metadata)

        # Store in ChromaDB
        collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id]
        )

        return doc_id

    def retrieve(
        self,
        query: str,
        categories: List[str] = None,
        n_results: int = 5,
        session_id: int = None
    ) -> List[Dict]:
        """
        Retrieve relevant content based on query.

        Args:
            query: The search query
            categories: Which collections to search (default: all)
            n_results: Number of results per category
            session_id: Filter to specific session

        Returns:
            List of relevant documents with metadata
        """
        if categories is None:
            categories = list(self.collections.keys())

        results = []

        for category in categories:
            if category not in self.collections:
                continue

            collection = self.collections[category]

            # Build where clause for filtering
            where = None
            if session_id:
                where = {"session_id": str(session_id)}

            # Query the collection
            query_results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            # Format results
            if query_results and query_results['documents']:
                for i, doc in enumerate(query_results['documents'][0]):
                    results.append({
                        "content": doc,
                        "category": category,
                        "metadata": query_results['metadatas'][0][i] if query_results['metadatas'] else {},
                        "distance": query_results['distances'][0][i] if query_results['distances'] else 0
                    })

        # Sort by relevance (lower distance = more relevant)
        results.sort(key=lambda x: x.get('distance', 0))

        return results[:n_results * 2]  # Return top results across all categories

    def store_decision(self, decision: str, context: str = None, tags: List[str] = None):
        """Convenience method for storing decisions."""
        content = f"DECISION: {decision}"
        if context:
            content += f"\nCONTEXT: {context}"

        metadata = {}
        if tags:
            metadata["tags"] = ",".join(tags)

        return self.store(content, "decisions", metadata)

    def store_code_change(self, summary: str, files: List[str], details: str = None):
        """Convenience method for storing code changes."""
        content = f"CODE CHANGE: {summary}\nFILES: {', '.join(files)}"
        if details:
            content += f"\nDETAILS: {details}"

        return self.store(content, "code_changes", {"files": ",".join(files)})

    def store_error(self, error: str, solution: str, file: str = None):
        """Convenience method for storing errors and their solutions."""
        content = f"ERROR: {error}\nSOLUTION: {solution}"
        if file:
            content += f"\nFILE: {file}"

        return self.store(content, "errors", {"resolved": "true"})

    def get_relevant_context(self, current_task: str, n_results: int = 5) -> str:
        """
        Get formatted relevant context for injection into prompts.

        Args:
            current_task: Description of what we're working on
            n_results: How many relevant items to retrieve

        Returns:
            Formatted string ready for context injection
        """
        results = self.retrieve(current_task, n_results=n_results)

        if not results:
            return ""

        context = "# Relevant History (from RAG)\n\n"

        for i, result in enumerate(results, 1):
            context += f"## [{result['category'].upper()}]\n"
            context += f"{result['content']}\n\n"

        return context

    def clear_category(self, category: str):
        """Clear all documents from a category (use with caution)."""
        if category in self.collections:
            self.client.delete_collection(category)
            self.collections[category] = self.client.create_collection(category)

    def get_stats(self) -> Dict:
        """Get statistics about stored content."""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = collection.count()
        stats["total"] = sum(stats.values())
        return stats
```

---

## Component 3: Context Assembler

### Location
`app/services/context_assembler.py` (new file)

### Purpose
Combines Baton + RAG + Current conversation into optimal context window.

### Implementation

```python
# app/services/context_assembler.py

from typing import Optional, List, Dict
from app.services.baton_service import EnhancedBatonService
from app.services.rag_service import RAGService

class ContextAssembler:
    """
    Assembles context from multiple sources into a single coherent prompt.
    Manages token budgets to fit within model limits.
    """

    # Token budget allocation (percentages of available context)
    BUDGET = {
        "baton": 0.15,      # 15% for current state
        "rag": 0.25,        # 25% for relevant history
        "current": 0.60,    # 60% for current conversation
    }

    def __init__(
        self,
        baton_service: EnhancedBatonService,
        rag_service: RAGService,
        max_context_tokens: int = 100000
    ):
        """
        Initialize Context Assembler.

        Args:
            baton_service: The Baton service instance
            rag_service: The RAG service instance
            max_context_tokens: Maximum tokens for context (model dependent)
        """
        self.baton = baton_service
        self.rag = rag_service
        self.max_tokens = max_context_tokens

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
            current_conversation: Recent messages
            baton_id: Specific baton to load (or uses latest)
            project_id: Project filter for baton
            include_rag: Whether to include RAG context
            include_baton: Whether to include Baton context

        Returns:
            Assembled context string ready for injection
        """
        context_parts = []

        # 1. Load Baton (current state)
        if include_baton:
            if baton_id:
                baton_content = self.baton.load_baton(baton_id)
            else:
                latest = self.baton.get_latest_baton(project_id)
                baton_content = self.baton.load_baton(latest.id) if latest else ""

            if baton_content:
                baton_tokens = self._count_tokens(baton_content)
                budget = int(self.max_tokens * self.BUDGET["baton"])

                if baton_tokens > budget:
                    baton_content = self._truncate(baton_content, budget)

                context_parts.append(baton_content)

        # 2. Retrieve RAG context (relevant history)
        if include_rag and current_task:
            rag_content = self.rag.get_relevant_context(current_task)

            if rag_content:
                rag_tokens = self._count_tokens(rag_content)
                budget = int(self.max_tokens * self.BUDGET["rag"])

                if rag_tokens > budget:
                    rag_content = self._truncate(rag_content, budget)

                context_parts.append(rag_content)

        # 3. Current conversation (already in context, just track budget)
        # This is handled by the caller, we just leave room for it

        # Combine all parts
        assembled = "\n\n---\n\n".join(context_parts)

        return assembled

    def get_context_health(self, current_tokens: int) -> Dict:
        """
        Get health status of context usage.

        Args:
            current_tokens: How many tokens are currently used

        Returns:
            Dict with health metrics
        """
        percentage = (current_tokens / self.max_tokens) * 100

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
            "percentage": percentage,
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
        """Rough token count estimate."""
        return len(text) // 4

    def _truncate(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit token budget."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[... truncated for context budget ...]"
```

---

## Integration Points

### 1. Roundtable Integration

In `roundtable_service.py`, modify `execute_round()`:

```python
def execute_round(self, round_id: int, context_assembler: ContextAssembler = None):
    # ... existing code ...

    # Inject assembled context into system prompt
    if context_assembler:
        assembled_context = context_assembler.assemble(
            current_task=round_obj.task_prompt,
            include_rag=True,
            include_baton=True
        )
        system_prompt = assembled_context + "\n\n" + system_prompt

    # ... rest of execution ...

    # After successful round, store in RAG
    if result["success"] and result["builder_response"]:
        self.rag.store_code_change(
            summary=round_obj.task_prompt,
            files=["auto-detected"],  # Could parse from response
            details=result["builder_response"].content[:500]
        )

        if result["consensus"] and result["consensus"]["passed"]:
            self.rag.store_decision(
                decision=f"Approved approach for: {round_obj.task_prompt}",
                context=result["builder_response"].content[:200]
            )
```

### 2. Auto-Baton Trigger

```python
def check_and_trigger_baton(self, context_assembler: ContextAssembler, current_tokens: int):
    """Automatically trigger baton creation when needed."""
    health = context_assembler.get_context_health(current_tokens)

    if health["should_baton"]:
        # Generate baton
        baton = self.baton_service.generate_baton(
            session_id=self.current_session_id,
            conversation_history=self.conversation_history
        )

        # Notify user
        return {
            "action": "baton_created",
            "baton_id": baton.id,
            "message": f"Context at {health['percentage']:.0f}%. Baton created for handoff."
        }

    return None
```

---

## UI Components

### Memory Status Panel

Add to `app/ui/roundtable_panel.py`:

```python
def render_memory_status(context_assembler, current_tokens):
    """Render memory system status."""
    health = context_assembler.get_context_health(current_tokens)
    rag_stats = context_assembler.rag.get_stats()

    st.subheader("Memory System Status")

    # Context Health Bar
    color_map = {"green": "normal", "yellow": "warning", "red": "error"}
    st.progress(health["percentage"] / 100)
    st.caption(f"{health['percentage']:.1f}% used | {health['remaining']:,} tokens remaining")
    st.caption(f"Status: {health['status'].upper()} - {health['recommendation']}")

    # RAG Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Decisions Stored", rag_stats.get("decisions", 0))
    with col2:
        st.metric("Code Changes", rag_stats.get("code_changes", 0))
    with col3:
        st.metric("Total Memories", rag_stats.get("total", 0))

    # Quick Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Baton Now"):
            # Trigger baton generation
            pass
    with col2:
        if st.button("View RAG Contents"):
            # Show RAG browser
            pass
```

---

## File Structure

```
app/
├── services/
│   ├── baton_service.py      # ENHANCE existing
│   ├── rag_service.py        # NEW
│   ├── context_assembler.py  # NEW
│   └── roundtable_service.py # MODIFY for integration
├── core/
│   └── models.py             # ADD BatonSnapshot model
└── ui/
    └── roundtable_panel.py   # ADD memory status UI

data/
└── chromadb/                 # NEW - RAG database storage
```

---

## Testing Checklist

- [ ] RAG stores and retrieves documents correctly
- [ ] Baton captures current state accurately
- [ ] Context Assembler respects token budgets
- [ ] Auto-baton triggers at 70% threshold
- [ ] Memory persists across sessions
- [ ] Roundtable injects assembled context
- [ ] UI shows accurate health status

---

## Success Criteria

The Memory System is complete when:

1. **Persistence**: Can start new session and have full context of previous work
2. **Retrieval**: Asking "what did we decide about X" returns accurate answer
3. **Automatic**: System stores important decisions without manual intervention
4. **Efficient**: Token budget is respected, no context overflow
5. **Visible**: User can see memory health and contents

---

*This is the foundation. Build this first, everything else depends on it.*
