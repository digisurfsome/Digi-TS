"""
Codebase Indexer Service

Indexes project files into RAG for retrieval during coding sessions.
Enables AI assistants to have codebase awareness through semantic search.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Set
from app.services.rag_service import RAGService
from app.services.process_log import ProcessLog


class CodebaseIndexer:
    """
    Indexes codebase files into RAG for semantic search.

    Usage:
        indexer = CodebaseIndexer()
        stats = indexer.index_directory("/path/to/project", project_id=1)
    """

    # File extensions to index by default
    SUPPORTED_EXTENSIONS: Set[str] = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.go', '.rs', '.rb', '.php',
        '.html', '.css', '.scss', '.vue', '.svelte',
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.sql', '.sh', '.bash', '.zsh'
    }

    # Directories to always skip
    SKIP_DIRS: Set[str] = {
        'node_modules', 'venv', '.venv', '__pycache__',
        '.git', '.svn', 'dist', 'build', '.next',
        'coverage', '.pytest_cache', '.mypy_cache',
        '.tox', 'eggs', '*.egg-info', '.eggs',
        'htmlcov', '.hypothesis', 'target'
    }

    # Maximum file size to index (500KB)
    MAX_FILE_SIZE: int = 500 * 1024

    # Maximum content length to store per file (10KB)
    MAX_CONTENT_LENGTH: int = 10000

    def __init__(self, rag_service: RAGService = None, persist_directory: str = "./data/chromadb"):
        """
        Initialize indexer.

        Args:
            rag_service: RAG service instance (creates new if None)
            persist_directory: ChromaDB storage path
        """
        self.rag = rag_service or RAGService(persist_directory=persist_directory)
        self.persist_directory = persist_directory

    def index_directory(
        self,
        directory: str,
        project_id: int,
        session_id: int = None,
        extensions: List[str] = None
    ) -> Dict:
        """
        Index all supported files in a directory recursively.

        Args:
            directory: Path to directory to index
            project_id: Project ID for RAG storage
            session_id: Optional session ID
            extensions: Optional list of extensions to include (overrides defaults)

        Returns:
            Dict with indexing statistics:
            {
                "files_found": int,
                "files_indexed": int,
                "files_skipped": int,
                "total_chars": int,
                "errors": List[str]
            }
        """
        stats = {
            "files_found": 0,
            "files_indexed": 0,
            "files_skipped": 0,
            "total_chars": 0,
            "errors": []
        }

        allowed_ext = set(extensions) if extensions else self.SUPPORTED_EXTENSIONS
        root_path = Path(directory).resolve()

        if not root_path.exists():
            ProcessLog.error("Indexer", f"Directory not found: {directory}")
            stats["errors"].append(f"Directory not found: {directory}")
            return stats

        if not root_path.is_dir():
            ProcessLog.error("Indexer", f"Path is not a directory: {directory}")
            stats["errors"].append(f"Path is not a directory: {directory}")
            return stats

        ProcessLog.info("Indexer", f"Starting index of {directory}", details={
            "extensions": list(allowed_ext)[:10],
            "project_id": project_id
        })

        for file_path in root_path.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip if in excluded directory
            if self._should_skip_path(file_path):
                continue

            # Check extension
            if file_path.suffix.lower() not in allowed_ext:
                continue

            stats["files_found"] += 1

            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size > self.MAX_FILE_SIZE:
                    stats["files_skipped"] += 1
                    continue
                if file_size == 0:
                    stats["files_skipped"] += 1
                    continue
            except OSError as e:
                stats["errors"].append(f"{file_path}: {str(e)}")
                stats["files_skipped"] += 1
                continue

            # Index the file
            try:
                doc_id = self._index_file(
                    file_path=file_path,
                    root_path=root_path,
                    project_id=project_id,
                    session_id=session_id
                )
                if doc_id:
                    stats["files_indexed"] += 1
                    stats["total_chars"] += file_size
                else:
                    stats["files_skipped"] += 1

            except Exception as e:
                stats["errors"].append(f"{file_path}: {str(e)}")
                stats["files_skipped"] += 1

        ProcessLog.success("Indexer", f"Indexed {stats['files_indexed']} files", details={
            "files_found": stats["files_found"],
            "files_indexed": stats["files_indexed"],
            "files_skipped": stats["files_skipped"],
            "total_chars": stats["total_chars"],
            "error_count": len(stats["errors"])
        })

        return stats

    def _should_skip_path(self, file_path: Path) -> bool:
        """Check if path should be skipped based on directory rules."""
        path_parts = file_path.parts
        for skip_dir in self.SKIP_DIRS:
            if skip_dir in path_parts:
                return True
        return False

    def _index_file(
        self,
        file_path: Path,
        root_path: Path,
        project_id: int,
        session_id: int = None
    ) -> Optional[str]:
        """
        Index a single file into RAG.

        Args:
            file_path: Absolute path to file
            root_path: Root directory for calculating relative path
            project_id: Project ID
            session_id: Optional session ID

        Returns:
            Document ID from RAG, or None if failed
        """
        # Read file content with encoding fallback
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding='latin-1')
            except Exception:
                return None

        if not content.strip():
            return None

        # Get relative path for cleaner storage
        try:
            relative_path = file_path.relative_to(root_path)
        except ValueError:
            relative_path = file_path.name

        # Truncate content if too long
        truncated_content = content[:self.MAX_CONTENT_LENGTH]
        was_truncated = len(content) > self.MAX_CONTENT_LENGTH

        # Build document for RAG
        doc_content = f"""FILE: {relative_path}
TYPE: {file_path.suffix}
SIZE: {len(content)} characters{' (truncated)' if was_truncated else ''}

CONTENT:
{truncated_content}
"""

        # Store in RAG as a spec (codebase file type)
        doc_id = self.rag.store_spec(
            spec_name=str(relative_path),
            content=doc_content,
            spec_type="codebase_file",
            project_id=project_id,
            session_id=session_id
        )

        return doc_id

    def index_single_file(
        self,
        file_path: str,
        project_id: int,
        session_id: int = None
    ) -> Optional[str]:
        """
        Index a single file by path.

        Args:
            file_path: Path to file (absolute or relative)
            project_id: Project ID
            session_id: Optional session ID

        Returns:
            Document ID or None if failed
        """
        path = Path(file_path).resolve()

        if not path.exists():
            ProcessLog.error("Indexer", f"File not found: {file_path}")
            return None

        if not path.is_file():
            ProcessLog.error("Indexer", f"Path is not a file: {file_path}")
            return None

        try:
            doc_id = self._index_file(
                file_path=path,
                root_path=path.parent,
                project_id=project_id,
                session_id=session_id
            )
            if doc_id:
                ProcessLog.success("Indexer", f"Indexed file: {file_path}")
            return doc_id
        except Exception as e:
            ProcessLog.error("Indexer", f"Failed to index {file_path}: {str(e)}")
            return None

    def clear_project_index(self, project_id: int) -> int:
        """
        Clear all indexed codebase files for a project.

        Args:
            project_id: Project ID to clear

        Returns:
            Number of documents deleted
        """
        deleted_count = 0

        try:
            # Get all specs for this project
            docs = self.rag.get_all_by_category("specs", project_id=project_id)

            for doc in docs:
                metadata = doc.get("metadata", {})
                if metadata.get("spec_type") == "codebase_file":
                    self.rag.delete_document(doc["id"], "specs")
                    deleted_count += 1

            ProcessLog.info("Indexer", f"Cleared {deleted_count} indexed files for project {project_id}")

        except Exception as e:
            ProcessLog.error("Indexer", f"Failed to clear index: {str(e)}")

        return deleted_count

    def get_index_stats(self, project_id: int) -> Dict:
        """
        Get statistics about indexed files for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with file count and other stats
        """
        try:
            docs = self.rag.get_all_by_category("specs", project_id=project_id)
            codebase_files = [
                d for d in docs
                if d.get("metadata", {}).get("spec_type") == "codebase_file"
            ]
            return {
                "indexed_files": len(codebase_files),
                "project_id": project_id
            }
        except Exception as e:
            ProcessLog.warning("Indexer", f"Failed to get stats: {str(e)}")
            return {"indexed_files": 0, "project_id": project_id, "error": str(e)}
