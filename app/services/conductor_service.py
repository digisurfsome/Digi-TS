"""
Conductor Service - The Orchestrator for Design Tree Studio.

Basic Haiku-powered orchestrator that coordinates:
- Memory System (RAG + Baton + Context Assembler)
- Round Table (multi-agent execution)
- Testing Facility (build-test loop)

Phase 4 of Bootstrap Sequence - Minimal Viable Orchestrator.

After this phase, the system can build itself.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re


class CommandType(Enum):
    """Types of commands the Conductor can handle."""
    BUILD = "build"
    TEST = "test"
    CHECKPOINT = "checkpoint"
    STATUS = "status"
    STORE = "store"
    QUERY = "query"
    EXECUTE = "execute"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class ConductorAction:
    """A single action to be executed."""
    action_type: str
    target: Any = None
    parameters: Dict = field(default_factory=dict)
    confirmation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type,
            "target": self.target,
            "parameters": self.parameters,
            "confirmation": self.confirmation
        }


@dataclass
class ConductorResult:
    """Result of a Conductor command execution."""
    success: bool
    actions: List[ConductorAction]
    results: List[Dict]
    confirmation: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "actions": [a.to_dict() for a in self.actions],
            "results": self.results,
            "confirmation": self.confirmation,
            "error": self.error
        }


class ConductorService:
    """
    The Conductor - orchestrates Memory, Round Table, and Testing.

    Uses a cheap, fast model (Haiku) for parsing and orchestration.
    This is the minimal viable orchestrator for Phase 4 bootstrap.

    Capabilities:
    - Parse simple natural language commands
    - Execute quick actions via buttons
    - Coordinate all three systems
    - Provide status and health checks
    """

    # Simple command patterns for local parsing (no API call needed)
    COMMAND_PATTERNS = {
        CommandType.BUILD: [
            r"run\s+(?:a\s+)?build",
            r"execute\s+(?:a\s+)?round",
            r"build\s+(?:the\s+)?code",
            r"start\s+(?:a\s+)?round",
        ],
        CommandType.TEST: [
            r"run\s+(?:the\s+)?tests?",
            r"test\s+(?:the\s+)?code",
            r"check\s+(?:the\s+)?code",
            r"validate",
        ],
        CommandType.CHECKPOINT: [
            r"create\s+(?:a\s+)?(?:checkpoint|baton)",
            r"save\s+(?:the\s+)?state",
            r"generate\s+(?:a\s+)?baton",
            r"snapshot",
        ],
        CommandType.STATUS: [
            r"(?:what(?:'s|s)?|show)\s+(?:the\s+)?(?:context\s+)?status",
            r"context\s+health",
            r"memory\s+status",
            r"system\s+status",
            r"how\s+(?:are\s+)?(?:we|things)",
        ],
        CommandType.STORE: [
            r"store\s+(?:this\s+)?decision",
            r"remember\s+(?:that|this)",
            r"save\s+(?:this\s+)?decision",
            r"record\s+(?:that|this)",
        ],
        CommandType.QUERY: [
            r"what\s+(?:did\s+we|have\s+we)",
            r"find\s+(?:decisions?|history)",
            r"search\s+(?:for|memory)",
            r"recall",
        ],
        CommandType.HELP: [
            r"help",
            r"what\s+can\s+you\s+do",
            r"commands?",
            r"how\s+(?:do\s+I|to)",
        ],
    }

    # Quick actions available for button-based UI
    QUICK_ACTIONS = {
        "run_build": {
            "name": "Run Build Round",
            "description": "Execute a build round with the current configuration",
            "icon": "🔨",
        },
        "run_tests": {
            "name": "Run Tests",
            "description": "Run all enabled test tiers",
            "icon": "🧪",
        },
        "create_checkpoint": {
            "name": "Create Checkpoint",
            "description": "Generate a baton snapshot of current state",
            "icon": "📍",
        },
        "check_status": {
            "name": "Check Status",
            "description": "Show context health and system status",
            "icon": "📊",
        },
        "run_full_cycle": {
            "name": "Full Build-Test Cycle",
            "description": "Build, test, and auto-fix until passing",
            "icon": "🔄",
        },
    }

    def __init__(
        self,
        roundtable_service=None,
        rag_service=None,
        context_assembler=None,
        testing_facility=None,
        baton_service=None,
        anthropic_key: str = None,
        use_ai_parsing: bool = False
    ):
        """
        Initialize the Conductor.

        Args:
            roundtable_service: RoundtableService instance for builds
            rag_service: RAGService instance for long-term memory
            context_assembler: ContextAssembler for context management
            testing_facility: TestingFacility for code testing
            baton_service: EnhancedBatonService for checkpoints
            anthropic_key: API key for Haiku (optional, for AI parsing)
            use_ai_parsing: Use Haiku for command parsing (default: False)
        """
        self.rt = roundtable_service
        self.rag = rag_service
        self.context = context_assembler
        self.tester = testing_facility
        self.baton = baton_service
        self.anthropic_key = anthropic_key
        self.use_ai_parsing = use_ai_parsing

        # Track current session/round for operations
        self.current_session_id: Optional[int] = None
        self.current_round_id: Optional[int] = None
        self.current_project_id: Optional[int] = None

        # Execution history for this session
        self.command_history: List[Dict] = []

        # Initialize Anthropic client if key provided
        self.anthropic_client = None
        if anthropic_key and use_ai_parsing:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                pass

    # =========================================================================
    # Command Processing
    # =========================================================================

    def process_command(
        self,
        user_input: str,
        session_context: Dict = None
    ) -> ConductorResult:
        """
        Process a natural language command from the user.

        Args:
            user_input: What the user said
            session_context: Optional current state information

        Returns:
            ConductorResult with actions taken and results
        """
        user_input = user_input.strip().lower()

        # Log the command
        self.command_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "input": user_input,
            "context": session_context
        })

        # Parse the command
        if self.use_ai_parsing and self.anthropic_client:
            actions = self._parse_with_ai(user_input, session_context)
        else:
            actions = self._parse_locally(user_input, session_context)

        # Execute the actions
        results = self._execute_actions(actions)

        # Build confirmation message
        confirmation = self._build_confirmation(actions, results)

        # Check for any errors
        has_error = any(not r.get("success", True) for r in results)

        return ConductorResult(
            success=not has_error,
            actions=actions,
            results=results,
            confirmation=confirmation,
            error=results[0].get("error") if has_error and results else None
        )

    def _parse_locally(
        self,
        user_input: str,
        context: Dict = None
    ) -> List[ConductorAction]:
        """Parse command using local pattern matching (no API call)."""
        user_lower = user_input.lower()

        # Try each command type
        for cmd_type, patterns in self.COMMAND_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_lower):
                    return self._create_actions_for_command(cmd_type, user_input, context)

        # Unknown command
        return [ConductorAction(
            action_type="help",
            confirmation="I didn't understand that command. Here's what I can do:"
        )]

    def _create_actions_for_command(
        self,
        cmd_type: CommandType,
        user_input: str,
        context: Dict = None
    ) -> List[ConductorAction]:
        """Create action list for a detected command type."""

        if cmd_type == CommandType.BUILD:
            return [ConductorAction(
                action_type="execute_round",
                target=self.current_round_id,
                confirmation="Executing build round..."
            )]

        elif cmd_type == CommandType.TEST:
            return [ConductorAction(
                action_type="run_tests",
                confirmation="Running test suite..."
            )]

        elif cmd_type == CommandType.CHECKPOINT:
            return [ConductorAction(
                action_type="create_baton",
                parameters={
                    "project_id": self.current_project_id,
                    "session_id": self.current_session_id
                },
                confirmation="Creating checkpoint..."
            )]

        elif cmd_type == CommandType.STATUS:
            return [ConductorAction(
                action_type="get_status",
                confirmation="Checking system status..."
            )]

        elif cmd_type == CommandType.STORE:
            # Extract the decision text after "store decision:"
            decision_match = re.search(
                r"(?:store|save|record|remember)\s+(?:this\s+)?(?:decision)?[:\s]+(.+)",
                user_input,
                re.IGNORECASE
            )
            decision_text = decision_match.group(1) if decision_match else user_input

            return [ConductorAction(
                action_type="store_decision",
                parameters={"decision": decision_text},
                confirmation=f"Storing decision: {decision_text[:50]}..."
            )]

        elif cmd_type == CommandType.QUERY:
            # Extract query text
            query_match = re.search(
                r"(?:what|find|search|recall)\s+(?:did\s+we|have\s+we|for)?\s*(.+)",
                user_input,
                re.IGNORECASE
            )
            query_text = query_match.group(1) if query_match else user_input

            return [ConductorAction(
                action_type="query_memory",
                parameters={"query": query_text},
                confirmation=f"Searching memory for: {query_text[:50]}..."
            )]

        elif cmd_type == CommandType.HELP:
            return [ConductorAction(
                action_type="show_help",
                confirmation="Showing available commands..."
            )]

        else:
            return [ConductorAction(
                action_type="unknown",
                confirmation="I didn't understand that. Type 'help' for available commands."
            )]

    def _parse_with_ai(
        self,
        user_input: str,
        context: Dict = None
    ) -> List[ConductorAction]:
        """Parse command using Haiku AI (costs money but more flexible)."""
        if not self.anthropic_client:
            return self._parse_locally(user_input, context)

        system_prompt = """You are the Conductor of Design Tree Studio, an AI coding system.
Parse the user's command and return a JSON array of actions to take.

Available actions:
- execute_round: Run a build round
- run_tests: Run the test suite
- create_baton: Create a checkpoint/baton
- get_status: Get system status
- store_decision: Store a decision in memory
- query_memory: Search memory for information
- show_help: Show available commands

Return JSON like:
[{"action_type": "execute_round", "target": null, "parameters": {}, "confirmation": "Executing build round..."}]
"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}]
            )

            # Parse JSON from response
            content = response.content[0].text
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                actions_data = json.loads(json_match.group())
                return [
                    ConductorAction(
                        action_type=a.get("action_type", "unknown"),
                        target=a.get("target"),
                        parameters=a.get("parameters", {}),
                        confirmation=a.get("confirmation", "")
                    )
                    for a in actions_data
                ]

        except Exception:
            pass

        # Fall back to local parsing
        return self._parse_locally(user_input, context)

    # =========================================================================
    # Action Execution
    # =========================================================================

    def _execute_actions(self, actions: List[ConductorAction]) -> List[Dict]:
        """Execute a list of actions and return results."""
        results = []

        for action in actions:
            result = {"action": action.action_type, "success": False}

            try:
                if action.action_type == "execute_round":
                    result = self._action_execute_round(action)

                elif action.action_type == "run_tests":
                    result = self._action_run_tests(action)

                elif action.action_type == "create_baton":
                    result = self._action_create_baton(action)

                elif action.action_type == "get_status":
                    result = self._action_get_status(action)

                elif action.action_type == "store_decision":
                    result = self._action_store_decision(action)

                elif action.action_type == "query_memory":
                    result = self._action_query_memory(action)

                elif action.action_type == "show_help":
                    result = self._action_show_help(action)

                else:
                    result = {
                        "action": action.action_type,
                        "success": False,
                        "error": f"Unknown action: {action.action_type}"
                    }

            except Exception as e:
                result = {
                    "action": action.action_type,
                    "success": False,
                    "error": str(e)
                }

            results.append(result)

        return results

    def _action_execute_round(self, action: ConductorAction) -> Dict:
        """Execute a build round via Round Table."""
        if not self.rt:
            return {"action": "execute_round", "success": False, "error": "Round Table not configured"}

        round_id = action.target or self.current_round_id
        if not round_id:
            return {"action": "execute_round", "success": False, "error": "No round specified"}

        try:
            # Use execute_round_with_testing if tester is available
            if self.tester:
                result = self.rt.execute_round_with_testing(
                    round_id=round_id,
                    auto_fix=True,
                    max_fix_iterations=3
                )
            else:
                result = self.rt.execute_round(round_id)

            return {
                "action": "execute_round",
                "success": result.get("success", False),
                "round_id": round_id,
                "result": result
            }
        except Exception as e:
            return {"action": "execute_round", "success": False, "error": str(e)}

    def _action_run_tests(self, action: ConductorAction) -> Dict:
        """Run the test suite."""
        if not self.tester:
            return {"action": "run_tests", "success": False, "error": "Testing Facility not configured"}

        try:
            # Get code from latest round if available
            code = action.parameters.get("code")

            if not code and self.rt and self.current_round_id:
                responses = self.rt.get_round_responses(self.current_round_id)
                if responses.get("builder") and responses["builder"]["response"]:
                    code = responses["builder"]["response"].content

            result = self.tester.run_all_tests(code=code)

            return {
                "action": "run_tests",
                "success": True,
                "all_passed": result.all_passed,
                "passed": result.passed,
                "failed": result.failed,
                "summary": self.tester.get_failure_summary(result) if not result.all_passed else "All tests passed!"
            }
        except Exception as e:
            return {"action": "run_tests", "success": False, "error": str(e)}

    def _action_create_baton(self, action: ConductorAction) -> Dict:
        """Create a checkpoint/baton."""
        if not self.baton:
            return {"action": "create_baton", "success": False, "error": "Baton Service not configured"}

        try:
            baton = self.baton.generate_baton(
                session_id=action.parameters.get("session_id") or self.current_session_id,
                project_id=action.parameters.get("project_id") or self.current_project_id,
                custom_sections=action.parameters.get("custom_sections")
            )

            return {
                "action": "create_baton",
                "success": True,
                "baton_id": baton.id,
                "message": f"Checkpoint created: {baton.snapshot_name}"
            }
        except Exception as e:
            return {"action": "create_baton", "success": False, "error": str(e)}

    def _action_get_status(self, action: ConductorAction) -> Dict:
        """Get system status including context health."""
        status = {
            "action": "get_status",
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "systems": {}
        }

        # Context health
        if self.context:
            try:
                # Estimate current tokens (rough)
                current_tokens = len(str(self.command_history)) // 4
                status["systems"]["context"] = self.context.get_context_health(current_tokens)
            except Exception as e:
                status["systems"]["context"] = {"error": str(e)}

        # RAG status
        if self.rag:
            try:
                status["systems"]["rag"] = self.rag.get_stats()
            except Exception as e:
                status["systems"]["rag"] = {"error": str(e)}

        # Round Table status
        if self.rt:
            try:
                status["systems"]["roundtable"] = {
                    "memory_enabled": getattr(self.rt, 'memory_enabled', False),
                    "testing_enabled": getattr(self.rt, 'testing_enabled', False),
                    "current_session": self.current_session_id,
                    "current_round": self.current_round_id
                }
            except Exception as e:
                status["systems"]["roundtable"] = {"error": str(e)}

        # Testing status
        if self.tester:
            try:
                status["systems"]["testing"] = {
                    "enabled_tiers": self.tester.enabled_tiers,
                    "project_path": self.tester.project_path
                }
            except Exception as e:
                status["systems"]["testing"] = {"error": str(e)}

        return status

    def _action_store_decision(self, action: ConductorAction) -> Dict:
        """Store a decision in RAG."""
        if not self.rag:
            return {"action": "store_decision", "success": False, "error": "RAG Service not configured"}

        decision = action.parameters.get("decision", "")
        if not decision:
            return {"action": "store_decision", "success": False, "error": "No decision provided"}

        try:
            doc_id = self.rag.store_decision(
                decision=decision,
                context=action.parameters.get("context"),
                project_id=self.current_project_id
            )

            return {
                "action": "store_decision",
                "success": True,
                "doc_id": doc_id,
                "message": f"Decision stored: {decision[:50]}..."
            }
        except Exception as e:
            return {"action": "store_decision", "success": False, "error": str(e)}

    def _action_query_memory(self, action: ConductorAction) -> Dict:
        """Query RAG for information."""
        if not self.rag:
            return {"action": "query_memory", "success": False, "error": "RAG Service not configured"}

        query = action.parameters.get("query", "")
        if not query:
            return {"action": "query_memory", "success": False, "error": "No query provided"}

        try:
            results = self.rag.retrieve(
                query=query,
                n_results=5,
                project_id=self.current_project_id
            )

            return {
                "action": "query_memory",
                "success": True,
                "results": results,
                "count": len(results),
                "message": f"Found {len(results)} relevant items"
            }
        except Exception as e:
            return {"action": "query_memory", "success": False, "error": str(e)}

    def _action_show_help(self, action: ConductorAction) -> Dict:
        """Show available commands and actions."""
        help_text = """
## Conductor Commands

**Build & Execute:**
- "Run a build round" - Execute the current round configuration
- "Execute round" - Same as above

**Testing:**
- "Run tests" - Run all enabled test tiers
- "Test the code" - Same as above

**Memory:**
- "Create a checkpoint" - Save current state as baton
- "Store decision: [text]" - Save a decision to memory
- "What did we decide about X?" - Query memory

**Status:**
- "What's the context status?" - Show system health
- "System status" - Same as above

**Quick Actions:** (for UI buttons)
"""
        for key, info in self.QUICK_ACTIONS.items():
            help_text += f"- {info['icon']} {info['name']}: {info['description']}\n"

        return {
            "action": "show_help",
            "success": True,
            "help_text": help_text,
            "quick_actions": self.QUICK_ACTIONS
        }

    def _build_confirmation(
        self,
        actions: List[ConductorAction],
        results: List[Dict]
    ) -> str:
        """Build human-readable confirmation of actions."""
        if not actions:
            return "No actions taken."

        lines = []
        for action, result in zip(actions, results):
            status = "✓" if result.get("success") else "✗"
            msg = action.confirmation or action.action_type
            if result.get("error"):
                msg += f" - Error: {result['error']}"
            elif result.get("message"):
                msg += f" - {result['message']}"
            lines.append(f"{status} {msg}")

        return "\n".join(lines)

    # =========================================================================
    # Quick Actions (for button-based UI)
    # =========================================================================

    def quick_action(self, action_name: str, **kwargs) -> Dict:
        """
        Execute a quick action by name.
        For button-based UI without natural language.

        Args:
            action_name: One of the QUICK_ACTIONS keys
            **kwargs: Additional parameters

        Returns:
            Action result dictionary
        """
        if action_name == "run_build":
            return self._action_execute_round(ConductorAction(
                action_type="execute_round",
                target=kwargs.get("round_id") or self.current_round_id
            ))

        elif action_name == "run_tests":
            return self._action_run_tests(ConductorAction(
                action_type="run_tests",
                parameters={"code": kwargs.get("code")}
            ))

        elif action_name == "create_checkpoint":
            return self._action_create_baton(ConductorAction(
                action_type="create_baton",
                parameters={
                    "project_id": kwargs.get("project_id") or self.current_project_id,
                    "session_id": kwargs.get("session_id") or self.current_session_id,
                    "custom_sections": kwargs.get("custom_sections")
                }
            ))

        elif action_name == "check_status":
            return self._action_get_status(ConductorAction(
                action_type="get_status"
            ))

        elif action_name == "run_full_cycle":
            return self._run_full_cycle(**kwargs)

        else:
            return {"success": False, "error": f"Unknown quick action: {action_name}"}

    def _run_full_cycle(self, **kwargs) -> Dict:
        """Run the complete build-test-fix cycle."""
        results = {
            "action": "run_full_cycle",
            "phases": [],
            "success": False
        }

        # Phase 1: Build
        build_result = self._action_execute_round(ConductorAction(
            action_type="execute_round",
            target=kwargs.get("round_id") or self.current_round_id
        ))
        results["phases"].append({"phase": "build", "result": build_result})

        if not build_result.get("success"):
            results["error"] = "Build phase failed"
            return results

        # Phase 2: Test (already included in execute_round_with_testing if tester available)
        if build_result.get("result", {}).get("all_tests_passed"):
            results["success"] = True
            results["message"] = "All tests passed!"
        elif build_result.get("result", {}).get("test_results"):
            # Tests ran but had failures
            results["test_summary"] = build_result["result"].get("loop_result", {}).get("remaining_failures")
            if build_result["result"].get("loop_result", {}).get("success"):
                results["success"] = True
                results["message"] = "Tests passed after fixes"
            else:
                results["message"] = "Some tests still failing after max iterations"
        else:
            results["success"] = True
            results["message"] = "Build completed (no tests configured)"

        # Phase 3: Store result in memory if successful
        if results["success"] and self.rag:
            try:
                self.rag.store_decision(
                    decision=f"Build cycle completed: {results.get('message', 'Success')}",
                    project_id=self.current_project_id
                )
            except Exception:
                pass

        return results

    # =========================================================================
    # Session Management
    # =========================================================================

    def set_context(
        self,
        session_id: int = None,
        round_id: int = None,
        project_id: int = None
    ):
        """Set the current session context for operations."""
        if session_id is not None:
            self.current_session_id = session_id
        if round_id is not None:
            self.current_round_id = round_id
        if project_id is not None:
            self.current_project_id = project_id

    def get_context(self) -> Dict:
        """Get the current session context."""
        return {
            "session_id": self.current_session_id,
            "round_id": self.current_round_id,
            "project_id": self.current_project_id
        }

    def get_command_history(self, limit: int = 10) -> List[Dict]:
        """Get recent command history."""
        return self.command_history[-limit:]

    # =========================================================================
    # System Integration Status
    # =========================================================================

    def get_integration_status(self) -> Dict:
        """Get status of all integrated systems."""
        return {
            "roundtable": {
                "available": self.rt is not None,
                "memory_enabled": getattr(self.rt, 'memory_enabled', False) if self.rt else False,
                "testing_enabled": getattr(self.rt, 'testing_enabled', False) if self.rt else False,
            },
            "rag": {
                "available": self.rag is not None,
                "stats": self.rag.get_stats() if self.rag else None,
            },
            "context_assembler": {
                "available": self.context is not None,
            },
            "testing_facility": {
                "available": self.tester is not None,
                "enabled_tiers": self.tester.enabled_tiers if self.tester else [],
            },
            "baton_service": {
                "available": self.baton is not None,
            },
            "ai_parsing": {
                "enabled": self.use_ai_parsing,
                "client_available": self.anthropic_client is not None,
            }
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_conductor(
    db_session=None,
    anthropic_key: str = None,
    openai_key: str = None,
    project_path: str = None
) -> ConductorService:
    """
    Create a fully configured Conductor with all integrations.

    Args:
        db_session: SQLAlchemy database session
        anthropic_key: Anthropic API key for AI models
        openai_key: OpenAI API key for AI models
        project_path: Path to project for testing

    Returns:
        Configured ConductorService instance
    """
    import os

    # Initialize services
    rag = None
    context = None
    baton = None
    rt = None
    tester = None

    # Try to initialize RAG
    try:
        from app.services.rag_service import RAGService
        rag = RAGService(persist_directory="./data/chromadb")
    except Exception:
        pass

    # Try to initialize Context Assembler
    if db_session:
        try:
            from app.services.context_assembler import ContextAssembler, EnhancedBatonService
            context = ContextAssembler(db=db_session, rag_service=rag)
            baton = EnhancedBatonService(db=db_session, rag_service=rag)
        except Exception:
            pass

    # Try to initialize Testing Facility
    try:
        from app.services.testing_facility import TestingFacility
        tester = TestingFacility(
            project_path=project_path or os.getcwd(),
            enabled_tiers=[1, 2, 3, 4, 5]
        )
    except Exception:
        pass

    # Try to initialize Roundtable
    if db_session:
        try:
            from app.services.roundtable_service import RoundtableService
            rt = RoundtableService(
                db=db_session,
                anthropic_key=anthropic_key,
                openai_key=openai_key,
                rag_service=rag,
                context_assembler=context,
                testing_facility=tester,
                project_path=project_path
            )
        except Exception:
            pass

    return ConductorService(
        roundtable_service=rt,
        rag_service=rag,
        context_assembler=context,
        testing_facility=tester,
        baton_service=baton,
        anthropic_key=anthropic_key,
        use_ai_parsing=False  # Default to local parsing
    )
