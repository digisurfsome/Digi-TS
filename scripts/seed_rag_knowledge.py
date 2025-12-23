#!/usr/bin/env python3
"""
Seed RAG Knowledge Base

Populates the RAG system with foundational knowledge from:
- Spec files in /specs/
- Architecture documentation
- Build plans and phases
- System understanding

Run this script to bootstrap the memory system with project knowledge.
Re-runnable: Will skip already-stored content based on hash.

Usage:
    python scripts/seed_rag_knowledge.py
    python scripts/seed_rag_knowledge.py --clear  # Clear and reseed
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_file_hash(content: str) -> str:
    """Generate hash for deduplication."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def chunk_text(text: str, max_chunk_size: int = 2000, overlap: int = 200) -> list:
    """
    Split text into overlapping chunks for better retrieval.

    Args:
        text: The text to chunk
        max_chunk_size: Max characters per chunk
        overlap: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chunk_size

        # Try to break at a paragraph or sentence
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + max_chunk_size // 2:
                end = para_break
            else:
                # Look for sentence break
                sent_break = text.rfind('. ', start, end)
                if sent_break > start + max_chunk_size // 2:
                    end = sent_break + 1

        chunks.append(text[start:end].strip())
        start = end - overlap

    return chunks


def seed_spec_files(rag, specs_dir: Path, verbose: bool = True):
    """Seed RAG with all spec files."""
    if not specs_dir.exists():
        print(f"  ⚠ Specs directory not found: {specs_dir}")
        return 0

    count = 0
    for spec_file in specs_dir.glob("*.md"):
        content = spec_file.read_text()
        filename = spec_file.name

        # Chunk large files
        chunks = chunk_text(content, max_chunk_size=3000)

        for i, chunk in enumerate(chunks):
            chunk_name = f"{filename}" if len(chunks) == 1 else f"{filename} (part {i+1}/{len(chunks)})"

            doc_id = rag.store(
                content=f"# SPEC: {chunk_name}\n\n{chunk}",
                category="specs",
                metadata={
                    "source": "spec_file",
                    "filename": filename,
                    "chunk": i + 1,
                    "total_chunks": len(chunks),
                    "seeded_at": datetime.now().isoformat()
                }
            )

            if verbose:
                print(f"  ✓ Stored: {chunk_name}")
            count += 1

    return count


def seed_architecture_knowledge(rag, verbose: bool = True):
    """Seed high-level architecture understanding."""

    architecture_docs = [
        {
            "name": "System Architecture Overview",
            "content": """
# Design Tree Studio - System Architecture

## Core Components

### 1. Memory System
- **Baton (Hot Memory)**: Current state, active task, recent context (~5-10k tokens)
- **RAG (Long Memory)**: Vector database storing all decisions, code changes, conversations
- **Context Assembler**: Combines Baton + RAG + Current conversation into optimal context

### 2. Round Table
- Multi-agent code generation system
- Builder agent writes code, Voter agents review
- Consensus mechanism for quality control
- Integrated with Testing Facility

### 3. Testing Facility
- 7-tier testing: Syntax, Static, Unit, Integration, App, Security, AI Review
- Build-Test Loop for automatic fix iterations
- Returns failures to Builder for correction

### 4. Conductor (Orchestrator)
- Natural language command parsing
- Quick action buttons for UI
- Coordinates all systems
- Simple commands: "run build", "run tests", "create checkpoint"

## Data Flow
User Input → Conductor → Round Table → Testing → Memory → Response
"""
        },
        {
            "name": "Bootstrap Phases",
            "content": """
# Bootstrap Sequence - Building a Self-Building System

## Completed Phases

### Phase 1: Memory System (Foundation)
- RAG service with ChromaDB
- Baton service for hot memory
- Context Assembler for token budgets
- Categories: decisions, code_changes, conversations, errors, specs

### Phase 2: Round Table + Memory Integration
- Multi-agent execution
- Auto-store decisions and code in RAG
- Context injection from memory

### Phase 3: Testing Facility + Build-Test Loop
- 5-tier testing (syntax, static, unit, integration, app)
- Automatic fix iterations
- Quality-checked code output

### Phase 4: Conductor (Basic Orchestrator)
- Command parsing (local pattern matching)
- Quick actions for UI
- System coordination
- BOOTSTRAP COMPLETE

## Future Phases

### Phase 5: Agent OS Integration
- Clone Agent OS repo
- Create adapter for task decomposition
- Connect to Round Table

### Phase 6: Design OS Integration
- Design document generation
- Spec-to-code translation

### Phase 7: Boilerplate Factory
- Template-based project generation
- Full automation pipeline
"""
        },
        {
            "name": "Memory System Design",
            "content": """
# Memory System Design Principles

## Token Budget Allocation
- Baton (hot memory): 15% of context
- RAG (long memory): 25% of context
- Current conversation: 60% of context

## Auto-Baton Trigger
- Triggers at 70% context usage
- Saves current state automatically
- Enables infinite context through handoffs

## RAG Categories
1. **decisions**: Architectural choices, approach selections
2. **code_changes**: What was built, file paths, summaries
3. **conversations**: Key discussion points
4. **errors**: What went wrong and fixes
5. **specs**: Requirements, constraints, plans

## Retrieval Strategy
- Semantic search using embeddings
- Filter by category, session, project
- Returns most relevant chunks
- Formatted for context injection
"""
        },
        {
            "name": "Round Table Mechanics",
            "content": """
# Round Table - Multi-Agent Code Generation

## Agent Roles
- **Builder**: Writes the code (typically Claude Opus or GPT-4)
- **Voter**: Reviews and votes on code quality
- **Reviewer**: Provides detailed feedback
- **Brainstormer**: Generates ideas (for design tasks)

## Execution Flow
1. Master prompt sets context and guardrails
2. Task prompt describes what to build
3. Builder generates code
4. Voters review with pass/fail vote
5. Consensus calculated (configurable threshold)
6. If passed: Store in memory, return code
7. If failed: Send feedback to Builder, iterate

## Integration Points
- Memory: Context injection, decision storage
- Testing: Auto-test after builds
- Conductor: Orchestration commands
"""
        },
        {
            "name": "Agent OS Integration Plan",
            "content": """
# Agent OS Integration (Phase 5+)

## What Agent OS Provides
- Task decomposition from high-level goals
- Planning engine with dependency graphs
- Workflow templates for common tasks
- Progress tracking and adjustment

## Integration Architecture
1. Clone Agent OS to external/agent-os
2. Create AgentOSAdapter for standardized interface
3. Wire into AgentOSIntegration service
4. Connect: Agent OS plans → Round Table executes → Testing validates

## Full Pipeline After Integration
User Goal → Design OS (spec) → Agent OS (plan) → Round Table (build) → Testing (validate) → Memory (store)

## Expected Outcome
- Reduces "vibe coding" from 1.5 days to 4 hours
- Automated task breakdown
- Quality-checked implementation
- Full project memory
"""
        }
    ]

    count = 0
    for doc in architecture_docs:
        doc_id = rag.store(
            content=doc["content"].strip(),
            category="specs",
            metadata={
                "source": "architecture",
                "name": doc["name"],
                "seeded_at": datetime.now().isoformat()
            }
        )
        if verbose:
            print(f"  ✓ Stored: {doc['name']}")
        count += 1

    return count


def seed_key_decisions(rag, verbose: bool = True):
    """Seed important project decisions."""

    decisions = [
        "Use ChromaDB for vector storage - lightweight, Python-native, good for prototyping",
        "Baton system for hot memory handoffs - enables infinite context across sessions",
        "Round Table with Builder/Voter pattern - quality through multi-agent consensus",
        "7-tier testing in Testing Facility - comprehensive quality gates",
        "Conductor uses local pattern matching first, AI parsing optional - fast and cheap",
        "Bootstrap sequence: Memory → Round Table → Testing → Conductor - each phase builds on previous",
        "Token budget: 15% baton, 25% RAG, 60% current conversation - balanced allocation",
        "Auto-baton triggers at 70% context usage - prevents overflow",
        "Phase 5+ integrates Agent OS and Design OS - external planning engines",
        "Boilerplate Factory built on top of full system - template-based project generation"
    ]

    count = 0
    for decision in decisions:
        doc_id = rag.store_decision(
            decision=decision,
            context="Project foundation decision from bootstrap sequence"
        )
        if verbose:
            print(f"  ✓ Decision: {decision[:60]}...")
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Seed RAG with project knowledge")
    parser.add_argument("--clear", action="store_true", help="Clear RAG before seeding")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    verbose = not args.quiet

    print("=" * 60)
    print("RAG Knowledge Base Seeder")
    print("=" * 60)

    # Initialize RAG
    try:
        from app.services.rag_service import RAGService
        rag = RAGService(persist_directory=str(PROJECT_ROOT / "data" / "chromadb"))
        print("✓ RAG service initialized")
    except ImportError as e:
        print(f"✗ Failed to import RAG service: {e}")
        print("  Make sure chromadb is installed: pip install chromadb")
        return 1
    except Exception as e:
        print(f"✗ Failed to initialize RAG: {e}")
        return 1

    # Clear if requested
    if args.clear:
        print("\n⚠ Clearing existing RAG data...")
        for category in rag.CATEGORIES:
            try:
                rag.clear_category(category)
                print(f"  ✓ Cleared: {category}")
            except Exception:
                pass

    # Get initial stats
    initial_stats = rag.get_stats()
    print(f"\nInitial RAG state: {initial_stats.get('total', 0)} documents")

    # Seed spec files
    print("\n--- Seeding Spec Files ---")
    specs_dir = PROJECT_ROOT / "specs"
    specs_count = seed_spec_files(rag, specs_dir, verbose)
    print(f"Added {specs_count} spec chunks")

    # Seed architecture knowledge
    print("\n--- Seeding Architecture Knowledge ---")
    arch_count = seed_architecture_knowledge(rag, verbose)
    print(f"Added {arch_count} architecture documents")

    # Seed key decisions
    print("\n--- Seeding Key Decisions ---")
    decisions_count = seed_key_decisions(rag, verbose)
    print(f"Added {decisions_count} decisions")

    # Final stats
    final_stats = rag.get_stats()
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"\nRAG Statistics:")
    for category, count in final_stats.items():
        if category != "total":
            print(f"  {category}: {count}")
    print(f"  ─────────────")
    print(f"  TOTAL: {final_stats.get('total', 0)}")

    print("\n✓ Knowledge base ready for retrieval")
    print("  Use: rag.retrieve('query') to search")
    print("  Use: rag.get_relevant_context('task') for formatted context")

    return 0


if __name__ == "__main__":
    sys.exit(main())
