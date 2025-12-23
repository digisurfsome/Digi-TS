"""
RAG (Retrieval-Augmented Generation) Service for long-term memory.

Stores and retrieves relevant context from all sessions using vector embeddings.
This is the "long memory" component of the Memory System.
"""

import hashlib
from typing import List, Dict, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class RAGService:
    """
    Long-term memory using vector database.
    Stores and retrieves relevant context from all sessions.
    """

    # Data categories for organization
    CATEGORIES = ["decisions", "code_changes", "conversations", "errors", "specs"]

    def __init__(self, persist_directory: str = "./data/chromadb"):
        """
        Initialize RAG service with ChromaDB.

        Args:
            persist_directory: Where to store the vector database
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is not installed. Install it with: pip install chromadb"
            )

        self.persist_directory = persist_directory

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )

        # Create collections for different content types
        self.collections = {}
        for category in self.CATEGORIES:
            self.collections[category] = self.client.get_or_create_collection(
                name=category,
                metadata={"description": f"Storage for {category}"}
            )

    def store(
        self,
        content: str,
        category: str,
        metadata: Dict = None,
        session_id: int = None,
        project_id: int = None
    ) -> str:
        """
        Store content in the appropriate collection.

        Args:
            content: The text to store
            category: One of: decisions, code_changes, conversations, errors, specs
            metadata: Additional metadata (tags, source, etc.)
            session_id: Optional session ID for filtering
            project_id: Optional project ID for filtering

        Returns:
            The document ID
        """
        if category not in self.collections:
            raise ValueError(f"Unknown category: {category}. Must be one of {self.CATEGORIES}")

        collection = self.collections[category]

        # Generate unique ID
        doc_id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        # Build metadata
        meta = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
        }
        if session_id:
            meta["session_id"] = str(session_id)
        if project_id:
            meta["project_id"] = str(project_id)
        if metadata:
            # Convert any non-string values to strings for ChromaDB
            for key, value in metadata.items():
                if isinstance(value, (list, dict)):
                    meta[key] = str(value)
                else:
                    meta[key] = str(value) if value is not None else ""

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
        session_id: int = None,
        project_id: int = None
    ) -> List[Dict]:
        """
        Retrieve relevant content based on query.

        Args:
            query: The search query
            categories: Which collections to search (default: all)
            n_results: Number of results per category
            session_id: Filter to specific session
            project_id: Filter to specific project

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
            where_conditions = []

            if session_id:
                where_conditions.append({"session_id": str(session_id)})
            if project_id:
                where_conditions.append({"project_id": str(project_id)})

            if len(where_conditions) == 1:
                where = where_conditions[0]
            elif len(where_conditions) > 1:
                where = {"$and": where_conditions}

            try:
                # Query the collection
                query_results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where
                )

                # Format results
                if query_results and query_results['documents'] and query_results['documents'][0]:
                    for i, doc in enumerate(query_results['documents'][0]):
                        results.append({
                            "content": doc,
                            "category": category,
                            "metadata": query_results['metadatas'][0][i] if query_results['metadatas'] else {},
                            "distance": query_results['distances'][0][i] if query_results.get('distances') else 0,
                            "id": query_results['ids'][0][i] if query_results.get('ids') else None
                        })
            except Exception as e:
                # Collection might be empty, continue to next
                continue

        # Sort by relevance (lower distance = more relevant)
        results.sort(key=lambda x: x.get('distance', 0))

        return results[:n_results * 2]  # Return top results across all categories

    def store_decision(
        self,
        decision: str,
        context: str = None,
        tags: List[str] = None,
        project_id: int = None,
        session_id: int = None
    ) -> str:
        """Convenience method for storing decisions."""
        content = f"DECISION: {decision}"
        if context:
            content += f"\nCONTEXT: {context}"

        metadata = {}
        if tags:
            metadata["tags"] = ",".join(tags)

        return self.store(
            content,
            "decisions",
            metadata,
            session_id=session_id,
            project_id=project_id
        )

    def store_code_change(
        self,
        summary: str,
        files: List[str],
        details: str = None,
        project_id: int = None,
        session_id: int = None
    ) -> str:
        """Convenience method for storing code changes."""
        content = f"CODE CHANGE: {summary}\nFILES: {', '.join(files)}"
        if details:
            content += f"\nDETAILS: {details}"

        return self.store(
            content,
            "code_changes",
            {"files": ",".join(files)},
            session_id=session_id,
            project_id=project_id
        )

    def store_error(
        self,
        error: str,
        solution: str,
        file: str = None,
        project_id: int = None,
        session_id: int = None
    ) -> str:
        """Convenience method for storing errors and their solutions."""
        content = f"ERROR: {error}\nSOLUTION: {solution}"
        if file:
            content += f"\nFILE: {file}"

        return self.store(
            content,
            "errors",
            {"resolved": "true", "file": file or ""},
            session_id=session_id,
            project_id=project_id
        )

    def store_spec(
        self,
        spec_name: str,
        content: str,
        spec_type: str = "requirement",
        project_id: int = None,
        session_id: int = None
    ) -> str:
        """Convenience method for storing specifications."""
        full_content = f"SPEC: {spec_name}\nTYPE: {spec_type}\nCONTENT: {content}"

        return self.store(
            full_content,
            "specs",
            {"spec_name": spec_name, "spec_type": spec_type},
            session_id=session_id,
            project_id=project_id
        )

    def store_conversation(
        self,
        summary: str,
        key_points: List[str] = None,
        project_id: int = None,
        session_id: int = None
    ) -> str:
        """Convenience method for storing conversation summaries."""
        content = f"CONVERSATION: {summary}"
        if key_points:
            content += f"\nKEY POINTS:\n- " + "\n- ".join(key_points)

        return self.store(
            content,
            "conversations",
            {"has_key_points": "true" if key_points else "false"},
            session_id=session_id,
            project_id=project_id
        )

    def get_relevant_context(
        self,
        current_task: str,
        n_results: int = 5,
        project_id: int = None
    ) -> str:
        """
        Get formatted relevant context for injection into prompts.

        Args:
            current_task: Description of what we're working on
            n_results: How many relevant items to retrieve
            project_id: Optional project filter

        Returns:
            Formatted string ready for context injection
        """
        results = self.retrieve(
            current_task,
            n_results=n_results,
            project_id=project_id
        )

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
            self.collections[category] = self.client.get_or_create_collection(
                name=category,
                metadata={"description": f"Storage for {category}"}
            )

    def clear_all(self):
        """Clear all documents from all categories (use with extreme caution)."""
        for category in self.CATEGORIES:
            self.clear_category(category)

    def get_stats(self) -> Dict:
        """Get statistics about stored content."""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = collection.count()
        stats["total"] = sum(stats.values())
        return stats

    def delete_document(self, doc_id: str, category: str) -> bool:
        """Delete a specific document by ID."""
        if category not in self.collections:
            return False

        try:
            self.collections[category].delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def get_all_by_category(
        self,
        category: str,
        limit: int = 100,
        project_id: int = None
    ) -> List[Dict]:
        """Get all documents from a category."""
        if category not in self.collections:
            return []

        collection = self.collections[category]

        where = None
        if project_id:
            where = {"project_id": str(project_id)}

        try:
            results = collection.get(
                limit=limit,
                where=where
            )

            documents = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    documents.append({
                        "content": doc,
                        "category": category,
                        "metadata": results['metadatas'][i] if results.get('metadatas') else {},
                        "id": results['ids'][i] if results.get('ids') else None
                    })
            return documents
        except Exception:
            return []
