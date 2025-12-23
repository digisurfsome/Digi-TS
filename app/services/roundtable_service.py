"""
Roundtable Coder service.

Handles session, round, and agent management for the Roundtable Coder feature.
Integrates with Memory System (Phase 2) for context injection and auto-storage.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import (
    RoundtableSession,
    RoundtableRound,
    RoundtableAgent,
    RoundtableResponse,
    RoundtableSessionStatus,
    AgentRole,
    VoteType,
)

# Memory System imports (Phase 2)
try:
    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False
    RAGService = None
    ContextAssembler = None

# Testing Facility imports (Phase 3)
try:
    from app.services.testing_facility import (
        TestingFacility,
        TestSuiteResult,
        TestStatus,
    )
    from app.services.build_test_loop import (
        BuildTestLoop,
        LoopResult,
        LoopStatus,
    )
    TESTING_SYSTEM_AVAILABLE = True
except ImportError:
    TESTING_SYSTEM_AVAILABLE = False
    TestingFacility = None
    TestSuiteResult = None
    BuildTestLoop = None


# Available models configuration
AVAILABLE_MODELS = {
    # Anthropic
    "Claude Opus 4.5": {
        "id": "claude-opus-4-5-20250101",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    "Claude Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    "Claude Sonnet 3.5": {
        "id": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    # OpenAI - GPT-5.x (Latest)
    "GPT-5.2": {
        "id": "gpt-5.2-2025-12-11",
        "provider": "openai",
        "max_tokens": 400000
    },
    "GPT-5.1": {
        "id": "gpt-5.1",
        "provider": "openai",
        "max_tokens": 400000
    },
    # OpenAI - GPT-4.x
    "GPT-4 Turbo": {
        "id": "gpt-4-turbo-preview",
        "provider": "openai",
        "max_tokens": 128000
    },
    "GPT-4o": {
        "id": "gpt-4o",
        "provider": "openai",
        "max_tokens": 128000
    },
    "GPT-4o Mini": {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "max_tokens": 128000
    },
    # OpenAI - o1 Reasoning
    "o1": {
        "id": "o1",
        "provider": "openai",
        "max_tokens": 200000
    },
    "o1-mini": {
        "id": "o1-mini",
        "provider": "openai",
        "max_tokens": 128000
    },
    # Google Gemini
    "Gemini 3 Pro": {
        "id": "gemini-3-pro-preview",
        "provider": "google",
        "max_tokens": 1048576
    },
    "Gemini 2.0 Flash Thinking": {
        "id": "gemini-2.0-flash-thinking-exp-1219",
        "provider": "google",
        "max_tokens": 1000000
    },
    "Gemini 2.0 Flash": {
        "id": "gemini-2.0-flash-exp",
        "provider": "google",
        "max_tokens": 1000000
    },
    "Gemini 1.5 Pro": {
        "id": "gemini-1.5-pro",
        "provider": "google",
        "max_tokens": 2000000
    },
    "Gemini 1.5 Flash": {
        "id": "gemini-1.5-flash",
        "provider": "google",
        "max_tokens": 1000000
    },
}

AGENT_ROLES = {
    "builder": "Write code based on the task prompt",
    "voter": "Review code and vote approve/reject with explanation",
    "reviewer": "Provide detailed code review without voting",
}

# Default prompts
DEFAULT_SYSTEM_PROMPT = """You are an expert software developer. Write clean, well-documented code.
Follow best practices and handle errors appropriately."""

DEFAULT_VOTER_PROMPT = """Review the code provided by the builder.

Your response MUST start with one of:
- APPROVE: [your explanation]
- REJECT: [your explanation with specific issues]

Be specific about what's good or what needs fixing."""


class RoundtableService:
    """Service for managing roundtable sessions, rounds, and agents."""

    def __init__(
        self,
        db: Session,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        google_key: Optional[str] = None,
        rag_service: Optional["RAGService"] = None,
        context_assembler: Optional["ContextAssembler"] = None,
        testing_facility: Optional["TestingFacility"] = None,
        project_path: Optional[str] = None
    ):
        """
        Initialize the RoundtableService.

        Args:
            db: SQLAlchemy database session
            anthropic_key: Anthropic API key (optional)
            openai_key: OpenAI API key (optional)
            google_key: Google AI API key (optional)
            rag_service: RAG service for long-term memory (Phase 2)
            context_assembler: Context assembler for memory integration (Phase 2)
            testing_facility: Testing facility for code validation (Phase 3)
            project_path: Project root path for testing (Phase 3)
        """
        self.db = db
        self.anthropic_client = None
        self.openai_client = None
        self.google_client = None
        self.google_key = google_key

        # Memory System integration (Phase 2)
        self.rag_service = rag_service
        self.context_assembler = context_assembler
        self.memory_enabled = MEMORY_SYSTEM_AVAILABLE and (rag_service is not None)

        # Testing System integration (Phase 3)
        self.testing_facility = testing_facility
        self.project_path = project_path
        self.testing_enabled = TESTING_SYSTEM_AVAILABLE and (testing_facility is not None)

        if anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            except ImportError:
                pass

        if openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_key)
            except ImportError:
                pass

        if google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.google_client = genai
            except ImportError:
                pass

    # =========================================================================
    # Session Management
    # =========================================================================

    def create_session(
        self,
        name: str,
        project_id: Optional[int] = None,
        master_prompt: Optional[str] = None,
        master_guardrails: Optional[str] = None,
        voting_threshold: float = 0.66,
        execution_mode: str = "single"
    ) -> RoundtableSession:
        """
        Create a new roundtable session.

        Args:
            name: Session name
            project_id: Optional project ID to link to
            master_prompt: System prompt for all agents
            master_guardrails: Guardrails/restrictions for agents
            voting_threshold: Percentage needed for consensus (0.0-1.0)
            execution_mode: "single" or "multi"

        Returns:
            Created RoundtableSession
        """
        session = RoundtableSession(
            name=name,
            project_id=project_id,
            master_prompt=master_prompt or DEFAULT_SYSTEM_PROMPT,
            master_guardrails=master_guardrails,
            voting_threshold=voting_threshold,
            execution_mode=execution_mode,
            status=RoundtableSessionStatus.ACTIVE,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: int) -> Optional[RoundtableSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            RoundtableSession or None
        """
        return self.db.query(RoundtableSession).filter(
            RoundtableSession.id == session_id
        ).first()

    def list_sessions(
        self,
        project_id: Optional[int] = None,
        include_completed: bool = True
    ) -> List[RoundtableSession]:
        """
        List all sessions, optionally filtered by project.

        Args:
            project_id: Filter by project ID (optional)
            include_completed: Include completed sessions

        Returns:
            List of RoundtableSession
        """
        query = self.db.query(RoundtableSession)

        if project_id is not None:
            query = query.filter(RoundtableSession.project_id == project_id)

        if not include_completed:
            query = query.filter(
                RoundtableSession.status != RoundtableSessionStatus.COMPLETED
            )

        return query.order_by(desc(RoundtableSession.created_at)).all()

    def update_session(
        self,
        session_id: int,
        **kwargs
    ) -> Optional[RoundtableSession]:
        """
        Update session settings.

        Args:
            session_id: Session ID
            **kwargs: Fields to update (name, master_prompt, master_guardrails,
                     voting_threshold, execution_mode, status)

        Returns:
            Updated RoundtableSession or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        allowed_fields = {
            'name', 'master_prompt', 'master_guardrails',
            'voting_threshold', 'execution_mode', 'status'
        }

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(session, key, value)

        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: int) -> bool:
        """
        Delete a session and all related data.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True

    # =========================================================================
    # Round Management
    # =========================================================================

    def add_round(
        self,
        session_id: int,
        name: Optional[str] = None,
        task_prompt: Optional[str] = None
    ) -> Optional[RoundtableRound]:
        """
        Add a round to a session.

        Args:
            session_id: Session ID
            name: Round name (optional)
            task_prompt: Task prompt for this round

        Returns:
            Created RoundtableRound or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Get next round number
        max_round = self.db.query(RoundtableRound).filter(
            RoundtableRound.session_id == session_id
        ).order_by(desc(RoundtableRound.round_number)).first()

        round_number = (max_round.round_number + 1) if max_round else 1

        round_obj = RoundtableRound(
            session_id=session_id,
            round_number=round_number,
            name=name or f"Round {round_number}",
            task_prompt=task_prompt,
            status="pending",
        )
        self.db.add(round_obj)
        self.db.commit()
        self.db.refresh(round_obj)
        return round_obj

    def get_round(self, round_id: int) -> Optional[RoundtableRound]:
        """
        Get a round by ID.

        Args:
            round_id: Round ID

        Returns:
            RoundtableRound or None
        """
        return self.db.query(RoundtableRound).filter(
            RoundtableRound.id == round_id
        ).first()

    def update_round(
        self,
        round_id: int,
        **kwargs
    ) -> Optional[RoundtableRound]:
        """
        Update round settings.

        Args:
            round_id: Round ID
            **kwargs: Fields to update (name, task_prompt, status)

        Returns:
            Updated RoundtableRound or None
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return None

        allowed_fields = {'name', 'task_prompt', 'status'}

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(round_obj, key, value)

        self.db.commit()
        self.db.refresh(round_obj)
        return round_obj

    def delete_round(self, round_id: int) -> bool:
        """
        Delete a round and all related agents/responses.

        Args:
            round_id: Round ID

        Returns:
            True if deleted, False if not found
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return False

        self.db.delete(round_obj)
        self.db.commit()
        return True

    # =========================================================================
    # Agent Management
    # =========================================================================

    def add_agent(
        self,
        round_id: int,
        model_name: str,
        role: str,
        prompt_override: Optional[str] = None
    ) -> Optional[RoundtableAgent]:
        """
        Add an agent to a round.

        Args:
            round_id: Round ID
            model_name: Model display name (key from AVAILABLE_MODELS)
            role: Agent role ("builder", "voter", "reviewer")
            prompt_override: Custom prompt for this agent (optional)

        Returns:
            Created RoundtableAgent or None if round not found or invalid model
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return None

        # Get model config
        model_config = AVAILABLE_MODELS.get(model_name)
        if not model_config:
            return None

        # Get next agent order
        max_agent = self.db.query(RoundtableAgent).filter(
            RoundtableAgent.round_id == round_id
        ).order_by(desc(RoundtableAgent.agent_order)).first()

        agent_order = (max_agent.agent_order + 1) if max_agent else 0

        # Convert role string to enum
        try:
            role_enum = AgentRole(role.lower())
        except ValueError:
            role_enum = AgentRole.BUILDER

        agent = RoundtableAgent(
            round_id=round_id,
            agent_order=agent_order,
            model=model_config["id"],
            provider=model_config["provider"],
            role=role_enum,
            prompt_override=prompt_override,
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def get_agent(self, agent_id: int) -> Optional[RoundtableAgent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            RoundtableAgent or None
        """
        return self.db.query(RoundtableAgent).filter(
            RoundtableAgent.id == agent_id
        ).first()

    def update_agent(
        self,
        agent_id: int,
        **kwargs
    ) -> Optional[RoundtableAgent]:
        """
        Update agent configuration.

        Args:
            agent_id: Agent ID
            **kwargs: Fields to update (model_name, role, prompt_override)

        Returns:
            Updated RoundtableAgent or None
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        # Handle model_name specially
        if 'model_name' in kwargs:
            model_config = AVAILABLE_MODELS.get(kwargs['model_name'])
            if model_config:
                agent.model = model_config["id"]
                agent.provider = model_config["provider"]

        # Handle role specially
        if 'role' in kwargs:
            try:
                agent.role = AgentRole(kwargs['role'].lower())
            except ValueError:
                pass

        # Handle prompt_override
        if 'prompt_override' in kwargs:
            agent.prompt_override = kwargs['prompt_override']

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        """
        Delete an agent and all responses.

        Args:
            agent_id: Agent ID

        Returns:
            True if deleted, False if not found
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        self.db.delete(agent)
        self.db.commit()
        return True

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def get_model_display_name(self, model_id: str) -> str:
        """
        Get display name for a model ID.

        Args:
            model_id: Model ID string

        Returns:
            Display name or the model ID if not found
        """
        for name, config in AVAILABLE_MODELS.items():
            if config["id"] == model_id:
                return name
        return model_id

    def get_session_with_rounds(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a session with all rounds and agents loaded.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with session data or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            "session": session,
            "rounds": [
                {
                    "round": r,
                    "agents": list(r.agents),
                    "responses": [
                        list(a.responses) for a in r.agents
                    ]
                }
                for r in session.rounds
            ]
        }

    # =========================================================================
    # Execution Engine (Phase C)
    # =========================================================================

    def call_agent(
        self,
        agent: RoundtableAgent,
        system_prompt: str,
        user_prompt: str,
        iteration: int = 1
    ) -> RoundtableResponse:
        """
        Make API call to a single agent and store response.

        Args:
            agent: The RoundtableAgent to call
            system_prompt: System prompt for the agent
            user_prompt: User prompt/task for the agent
            iteration: Iteration number for this response

        Returns:
            RoundtableResponse with the agent's response

        Raises:
            ValueError: If the required API client is not configured
        """
        import time

        start_time = time.time()
        content = ""
        tokens_in = 0
        tokens_out = 0
        cost = 0.0

        if agent.provider == "anthropic":
            if not self.anthropic_client:
                raise ValueError("Anthropic API key not configured")

            response = self.anthropic_client.messages.create(
                model=agent.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            content = response.content[0].text
            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens
            # Estimate cost (Sonnet 3.5 pricing as baseline)
            cost = (tokens_in * 0.003 / 1000) + (tokens_out * 0.015 / 1000)

        elif agent.provider == "openai":
            if not self.openai_client:
                raise ValueError("OpenAI API key not configured")

            response = self.openai_client.chat.completions.create(
                model=agent.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.choices[0].message.content
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
            # Estimate cost (GPT-4o pricing as baseline, GPT-5.x is more expensive)
            if "gpt-5" in agent.model:
                cost = (tokens_in * 1.75 / 1000000) + (tokens_out * 14.0 / 1000000)
            else:
                cost = (tokens_in * 0.005 / 1000) + (tokens_out * 0.015 / 1000)

        elif agent.provider == "google":
            if not self.google_client:
                raise ValueError("Google AI API key not configured")

            # Combine system prompt with user prompt for Gemini
            combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

            model = self.google_client.GenerativeModel(agent.model)
            response = model.generate_content(combined_prompt)

            content = response.text
            # Gemini token counting (approximate if not available)
            try:
                tokens_in = response.usage_metadata.prompt_token_count
                tokens_out = response.usage_metadata.candidates_token_count
            except AttributeError:
                # Estimate tokens if metadata not available
                tokens_in = len(combined_prompt) // 4
                tokens_out = len(content) // 4

            # Gemini pricing (Gemini 1.5 Pro pricing as baseline)
            cost = (tokens_in * 0.00125 / 1000) + (tokens_out * 0.005 / 1000)

        else:
            raise ValueError(f"Unknown provider: {agent.provider}")

        duration = time.time() - start_time

        # Parse vote if this is a voter agent
        vote = None
        vote_reason = None
        if agent.role == AgentRole.VOTER:
            vote, vote_reason = self._parse_vote(content)

        # Create and store response
        response_obj = RoundtableResponse(
            agent_id=agent.id,
            iteration=iteration,
            content=content,
            vote=vote,
            vote_reason=vote_reason,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost=cost,
            duration_seconds=duration,
        )
        self.db.add(response_obj)
        self.db.commit()
        self.db.refresh(response_obj)

        return response_obj

    def _parse_vote(self, content: str) -> tuple:
        """
        Parse vote from voter response content.

        Args:
            content: The response content to parse

        Returns:
            Tuple of (VoteType or None, reason string or None)
        """
        if not content:
            return None, None

        content_upper = content.upper().strip()

        if content_upper.startswith("APPROVE"):
            # Extract reason after "APPROVE:"
            reason = content.split(":", 1)[1].strip() if ":" in content else content
            return VoteType.APPROVE, reason

        elif content_upper.startswith("REJECT"):
            reason = content.split(":", 1)[1].strip() if ":" in content else content
            return VoteType.REJECT, reason

        elif content_upper.startswith("ABSTAIN"):
            reason = content.split(":", 1)[1].strip() if ":" in content else content
            return VoteType.ABSTAIN, reason

        # Try to infer from content
        if "APPROVE" in content_upper[:100]:
            return VoteType.APPROVE, content
        elif "REJECT" in content_upper[:100]:
            return VoteType.REJECT, content

        return VoteType.ABSTAIN, content

    def execute_round(
        self,
        round_id: int,
        execution_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute all agents in a round.

        Args:
            round_id: The round to execute
            execution_mode: "single" (builder only) or "multi" (builder + voters)
                           If None, uses the session's execution_mode

        Returns:
            Dictionary with execution results:
            {
                "success": bool,
                "error": str or None,
                "builder_response": RoundtableResponse or None,
                "voter_responses": List[RoundtableResponse],
                "consensus": dict from calculate_consensus(),
                "memory_stored": bool (Phase 2)
            }
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return {"success": False, "error": "Round not found"}

        session = round_obj.session
        mode = execution_mode or session.execution_mode

        # Update round status
        round_obj.status = "running"
        self.db.commit()

        # Build system prompt
        system_prompt = session.master_prompt or DEFAULT_SYSTEM_PROMPT
        if session.master_guardrails:
            system_prompt += f"\n\n## Guardrails\n{session.master_guardrails}"

        # PHASE 2: Inject assembled context from Memory System
        assembled_context = ""
        if self.memory_enabled and self.context_assembler:
            try:
                assembled_context = self.context_assembler.assemble(
                    current_task=round_obj.task_prompt or "",
                    project_id=session.project_id,
                    include_rag=True,
                    include_baton=True
                )
                if assembled_context:
                    system_prompt = assembled_context + "\n\n---\n\n" + system_prompt
            except Exception as e:
                # Don't fail execution if memory system has issues
                pass

        # Get agents sorted by order
        agents = sorted(round_obj.agents, key=lambda a: a.agent_order)

        if not agents:
            round_obj.status = "completed"
            round_obj.completed_at = datetime.utcnow()
            self.db.commit()
            return {"success": False, "error": "No agents configured for this round"}

        # Find builder and voters
        builders = [a for a in agents if a.role == AgentRole.BUILDER]
        voters = [a for a in agents if a.role == AgentRole.VOTER]
        reviewers = [a for a in agents if a.role == AgentRole.REVIEWER]

        if not builders:
            round_obj.status = "completed"
            round_obj.completed_at = datetime.utcnow()
            self.db.commit()
            return {"success": False, "error": "No builder agent configured"}

        result = {
            "success": True,
            "error": None,
            "builder_response": None,
            "voter_responses": [],
            "reviewer_responses": [],
            "consensus": None,
        }

        try:
            # Execute builder first
            builder = builders[0]
            builder_prompt = builder.prompt_override or round_obj.task_prompt or ""

            builder_response = self.call_agent(
                agent=builder,
                system_prompt=system_prompt,
                user_prompt=builder_prompt,
            )
            result["builder_response"] = builder_response

            # If multi-agent mode, run voters with builder's output
            if mode == "multi" and (voters or reviewers):
                builder_output = builder_response.content

                # Execute voters
                for voter in voters:
                    voter_system = system_prompt + "\n\n" + DEFAULT_VOTER_PROMPT
                    voter_prompt = f"""## Builder's Code Output

{builder_output}

## Original Task
{round_obj.task_prompt or 'No task specified'}

Please review the builder's code and provide your vote."""

                    if voter.prompt_override:
                        voter_prompt = voter.prompt_override + "\n\n" + voter_prompt

                    voter_response = self.call_agent(
                        agent=voter,
                        system_prompt=voter_system,
                        user_prompt=voter_prompt,
                    )
                    result["voter_responses"].append(voter_response)

                # Execute reviewers (no voting)
                for reviewer in reviewers:
                    reviewer_prompt = f"""## Builder's Code Output

{builder_output}

## Original Task
{round_obj.task_prompt or 'No task specified'}

Please provide a detailed code review."""

                    if reviewer.prompt_override:
                        reviewer_prompt = reviewer.prompt_override + "\n\n" + reviewer_prompt

                    reviewer_response = self.call_agent(
                        agent=reviewer,
                        system_prompt=system_prompt,
                        user_prompt=reviewer_prompt,
                    )
                    result["reviewer_responses"].append(reviewer_response)

                # Calculate consensus
                result["consensus"] = self.calculate_consensus(round_id)

                # Update round with consensus info
                if result["consensus"]:
                    round_obj.consensus_reached = result["consensus"]["passed"]
                    round_obj.consensus_percentage = result["consensus"]["percentage"]

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        # Mark round as completed
        round_obj.status = "completed"
        round_obj.completed_at = datetime.utcnow()
        self.db.commit()

        # PHASE 2: Auto-store in RAG after successful execution
        result["memory_stored"] = False
        if result["success"] and self.memory_enabled and self.rag_service:
            try:
                # Store code change if builder produced output
                if result.get("builder_response") and result["builder_response"].content:
                    self.rag_service.store_code_change(
                        summary=round_obj.task_prompt or "Roundtable build",
                        files=["roundtable-output"],
                        details=result["builder_response"].content[:500],
                        project_id=session.project_id,
                        session_id=session.id
                    )

                # Store decision if consensus was reached
                if result.get("consensus") and result["consensus"].get("passed"):
                    self.rag_service.store_decision(
                        decision=f"Approved: {round_obj.task_prompt or 'Roundtable task'}",
                        context=f"Consensus: {result['consensus']['percentage']*100:.0f}% approval",
                        project_id=session.project_id,
                        session_id=session.id
                    )

                result["memory_stored"] = True
            except Exception as e:
                # Don't fail the result if memory storage fails
                result["memory_error"] = str(e)

        return result

    def calculate_consensus(self, round_id: int) -> Dict[str, Any]:
        """
        Calculate voting consensus for a round.

        Args:
            round_id: Round ID

        Returns:
            Dictionary with consensus information:
            {
                "total_voters": int,
                "approvals": int,
                "rejections": int,
                "abstentions": int,
                "percentage": float (0.0-1.0),
                "threshold": float,
                "passed": bool,
                "feedback": list[str]  # Voter feedback for builder
            }
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return {}

        session = round_obj.session

        # Get all voter responses for this round
        voters = [a for a in round_obj.agents if a.role == AgentRole.VOTER]

        approvals = 0
        rejections = 0
        abstentions = 0
        feedback = []

        for voter in voters:
            # Get the latest response for this voter
            latest_response = self.db.query(RoundtableResponse).filter(
                RoundtableResponse.agent_id == voter.id
            ).order_by(desc(RoundtableResponse.iteration)).first()

            if latest_response and latest_response.vote:
                if latest_response.vote == VoteType.APPROVE:
                    approvals += 1
                elif latest_response.vote == VoteType.REJECT:
                    rejections += 1
                    # Collect rejection feedback
                    if latest_response.vote_reason:
                        feedback.append(latest_response.vote_reason)
                else:
                    abstentions += 1

        total_voters = len(voters)
        # Calculate percentage (excluding abstentions from denominator)
        voting_count = approvals + rejections
        percentage = approvals / voting_count if voting_count > 0 else 0.0

        threshold = session.voting_threshold
        passed = percentage >= threshold

        return {
            "total_voters": total_voters,
            "approvals": approvals,
            "rejections": rejections,
            "abstentions": abstentions,
            "percentage": percentage,
            "threshold": threshold,
            "passed": passed,
            "feedback": feedback,
        }

    # =========================================================================
    # Phase 3: Testing System Integration
    # =========================================================================

    def execute_round_with_testing(
        self,
        round_id: int,
        execution_mode: Optional[str] = None,
        auto_fix: bool = True,
        max_fix_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a round and automatically run tests.
        Optionally auto-fix if tests fail.

        Args:
            round_id: Round ID to execute
            execution_mode: "single" or "multi"
            auto_fix: Whether to auto-fix on test failures
            max_fix_iterations: Maximum fix iterations

        Returns:
            Dictionary with execution results including test results
        """
        # Execute initial build round
        result = self.execute_round(round_id, execution_mode)

        if not result.get("success"):
            return result

        # Run tests if testing is enabled and builder produced output
        if self.testing_enabled and self.testing_facility:
            if result.get("builder_response") and result["builder_response"].content:
                code = result["builder_response"].content
                test_result = self.testing_facility.run_all_tests(code=code)
                result["test_results"] = test_result.to_dict()
                result["all_tests_passed"] = test_result.all_passed

                # Auto-fix loop if enabled and tests failed
                if auto_fix and not test_result.all_passed:
                    loop_result = self._run_fix_loop(
                        round_id=round_id,
                        initial_code=code,
                        initial_test_result=test_result,
                        max_iterations=max_fix_iterations
                    )
                    result["loop_result"] = loop_result
                    if loop_result.get("success"):
                        result["final_code"] = loop_result.get("final_code")
                        result["all_tests_passed"] = True

        return result

    def _run_fix_loop(
        self,
        round_id: int,
        initial_code: str,
        initial_test_result: "TestSuiteResult",
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Run the fix loop to resolve test failures.

        Args:
            round_id: Round ID for context
            initial_code: Code that failed tests
            initial_test_result: Initial test results
            max_iterations: Maximum fix attempts

        Returns:
            Dictionary with loop results
        """
        if not TESTING_SYSTEM_AVAILABLE:
            return {"success": False, "error": "Testing system not available"}

        round_obj = self.get_round(round_id)
        if not round_obj:
            return {"success": False, "error": "Round not found"}

        current_code = initial_code
        test_result = initial_test_result
        history = []

        for iteration in range(1, max_iterations + 1):
            # Build fix prompt
            failures = self.testing_facility.get_failure_summary(test_result)
            fix_prompt = f"""The previous code has test failures that need to be fixed.

## Previous Code
```python
{current_code[:5000]}
```

## Test Failures
{failures}

## Your Task
Fix the code to make all tests pass. Only modify what's necessary.
Return the complete fixed code.
"""

            # Update round task and execute
            self.update_round(round_id, task_prompt=fix_prompt)
            fix_result = self.execute_round(round_id)

            if not fix_result.get("success"):
                history.append({
                    "iteration": iteration,
                    "phase": "build",
                    "success": False,
                    "error": fix_result.get("error")
                })
                continue

            if fix_result.get("builder_response"):
                current_code = fix_result["builder_response"].content

            # Test the fixed code
            test_result = self.testing_facility.run_all_tests(code=current_code)

            history.append({
                "iteration": iteration,
                "phase": "test",
                "success": test_result.all_passed,
                "passed": test_result.passed,
                "failed": test_result.failed
            })

            if test_result.all_passed:
                return {
                    "success": True,
                    "final_code": current_code,
                    "iterations": iteration,
                    "history": history,
                    "message": f"All tests passed after {iteration} fix iteration(s)"
                }

        # Max iterations reached
        return {
            "success": False,
            "final_code": current_code,
            "iterations": max_iterations,
            "history": history,
            "message": f"Max iterations ({max_iterations}) reached",
            "remaining_failures": self.testing_facility.get_failure_summary(test_result)
        }

    def test_round_output(self, round_id: int) -> Dict[str, Any]:
        """
        Test the latest builder response from a round.

        Args:
            round_id: Round ID to test

        Returns:
            Dictionary with test results
        """
        if not self.testing_enabled:
            return {"success": False, "error": "Testing not enabled"}

        responses = self.get_round_responses(round_id)

        if not responses.get("builder") or not responses["builder"]["response"]:
            return {"success": False, "error": "No builder response found"}

        code = responses["builder"]["response"].content
        test_result = self.testing_facility.run_all_tests(code=code)

        return {
            "success": True,
            "test_results": test_result.to_dict(),
            "all_passed": test_result.all_passed,
            "summary": self.testing_facility.get_failure_summary(test_result)
        }

    def get_testing_status(self) -> Dict[str, Any]:
        """
        Get current status of the Testing System integration.

        Returns:
            Dictionary with testing system status
        """
        return {
            "enabled": self.testing_enabled,
            "available": TESTING_SYSTEM_AVAILABLE,
            "facility_configured": self.testing_facility is not None,
            "project_path": self.project_path,
            "enabled_tiers": (
                self.testing_facility.enabled_tiers
                if self.testing_facility else []
            )
        }

    # =========================================================================
    # Additional Round Methods
    # =========================================================================

    def list_rounds(self, session_id: int) -> List[RoundtableRound]:
        """
        List all rounds for a session.

        Args:
            session_id: Session ID

        Returns:
            List of RoundtableRound objects
        """
        return self.db.query(RoundtableRound).filter(
            RoundtableRound.session_id == session_id
        ).order_by(RoundtableRound.round_number).all()

    def get_round_responses(self, round_id: int) -> Dict[str, Any]:
        """
        Get all responses for a round organized by role.

        Args:
            round_id: Round ID

        Returns:
            Dictionary with builder and voter responses
        """
        round_obj = self.get_round(round_id)
        if not round_obj:
            return {"builder": None, "voters": [], "reviewers": []}

        builder_response = None
        voter_responses = []
        reviewer_responses = []

        for agent in round_obj.agents:
            # Get latest response for this agent
            latest = self.db.query(RoundtableResponse).filter(
                RoundtableResponse.agent_id == agent.id
            ).order_by(desc(RoundtableResponse.iteration)).first()

            if not latest:
                continue

            response_data = {
                "agent": agent,
                "response": latest,
                "model": self.get_model_display_name(agent.model)
            }

            if agent.role == AgentRole.BUILDER:
                builder_response = response_data
            elif agent.role == AgentRole.VOTER:
                voter_responses.append(response_data)
            elif agent.role == AgentRole.REVIEWER:
                reviewer_responses.append(response_data)

        return {
            "builder": builder_response,
            "voters": voter_responses,
            "reviewers": reviewer_responses
        }

    # =========================================================================
    # Phase F: Baton Integration
    # =========================================================================

    def generate_roundtable_baton(self, session_id: int) -> str:
        """
        Generate a baton snapshot for a roundtable session.

        Args:
            session_id: Session ID

        Returns:
            Baton content as markdown string
        """
        session = self.get_session(session_id)
        if not session:
            return "Session not found"

        rounds = self.list_rounds(session_id)

        # Build context from all rounds and responses
        context = f"# Roundtable Session: {session.name}\n\n"
        context += f"**Execution Mode:** {session.execution_mode}\n"
        context += f"**Voting Threshold:** {session.voting_threshold * 100:.0f}%\n"
        context += f"**Status:** {session.status.value if hasattr(session.status, 'value') else session.status}\n\n"

        if session.master_prompt:
            context += f"## Master Prompt\n{session.master_prompt[:500]}...\n\n"

        if session.master_guardrails:
            context += f"## Guardrails\n{session.master_guardrails}\n\n"

        context += "## Rounds\n\n"

        for round_obj in rounds:
            context += f"### Round {round_obj.round_number}: {round_obj.name}\n"
            context += f"**Task:** {round_obj.task_prompt or 'No task specified'}\n"
            context += f"**Status:** {round_obj.status}\n\n"

            # Add responses
            responses = self.get_round_responses(round_obj.id)

            if responses["builder"] and responses["builder"]["response"]:
                builder_resp = responses["builder"]["response"]
                content_preview = builder_resp.content[:2000] if builder_resp.content else "No content"
                context += f"#### Builder Response ({responses['builder']['model']})\n"
                context += f"```\n{content_preview}\n```\n\n"

            if responses["voters"]:
                context += "#### Voter Responses\n"
                for voter_data in responses["voters"]:
                    voter_resp = voter_data["response"]
                    vote_str = voter_resp.vote.value if voter_resp.vote else "No vote"
                    context += f"- **{voter_data['model']}**: {vote_str}\n"
                context += "\n"

            # Add consensus info if available
            if round_obj.consensus_reached is not None:
                consensus_status = "✅ Reached" if round_obj.consensus_reached else "❌ Not reached"
                context += f"**Consensus:** {consensus_status}"
                if round_obj.consensus_percentage is not None:
                    context += f" ({round_obj.consensus_percentage * 100:.0f}%)"
                context += "\n\n"

        context += f"\n---\n*Generated at: {datetime.utcnow().isoformat()}*\n"

        return context

    # =========================================================================
    # Phase I: Audit & Statistics
    # =========================================================================

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """
        Get statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with session statistics
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        rounds = self.list_rounds(session_id)

        total_cost = 0.0
        total_tokens_in = 0
        total_tokens_out = 0
        completed_rounds = 0
        total_responses = 0

        for round_obj in rounds:
            if round_obj.status == "completed":
                completed_rounds += 1

            responses = self.get_round_responses(round_obj.id)

            # Process builder response
            if responses["builder"] and responses["builder"]["response"]:
                r = responses["builder"]["response"]
                total_cost += r.cost or 0
                total_tokens_in += r.tokens_input or 0
                total_tokens_out += r.tokens_output or 0
                total_responses += 1

            # Process voter responses
            for voter_data in responses["voters"]:
                if voter_data["response"]:
                    r = voter_data["response"]
                    total_cost += r.cost or 0
                    total_tokens_in += r.tokens_input or 0
                    total_tokens_out += r.tokens_output or 0
                    total_responses += 1

            # Process reviewer responses
            for reviewer_data in responses["reviewers"]:
                if reviewer_data["response"]:
                    r = reviewer_data["response"]
                    total_cost += r.cost or 0
                    total_tokens_in += r.tokens_input or 0
                    total_tokens_out += r.tokens_output or 0
                    total_responses += 1

        return {
            "total_rounds": len(rounds),
            "completed_rounds": completed_rounds,
            "total_responses": total_responses,
            "total_cost": total_cost,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_tokens": total_tokens_in + total_tokens_out,
        }

    def export_session(self, session_id: int) -> Dict[str, Any]:
        """
        Export entire session as JSON for backup/transfer.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with full session data
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        rounds = self.list_rounds(session_id)
        stats = self.get_session_stats(session_id)

        rounds_data = []
        for r in rounds:
            responses = self.get_round_responses(r.id)
            round_data = {
                "round_number": r.round_number,
                "name": r.name,
                "task_prompt": r.task_prompt,
                "status": r.status,
                "consensus_reached": r.consensus_reached,
                "consensus_percentage": r.consensus_percentage,
                "responses": {
                    "builder": None,
                    "voters": [],
                    "reviewers": []
                }
            }

            if responses["builder"] and responses["builder"]["response"]:
                br = responses["builder"]["response"]
                round_data["responses"]["builder"] = {
                    "model": responses["builder"]["model"],
                    "content": br.content,
                    "tokens_in": br.tokens_input,
                    "tokens_out": br.tokens_output,
                    "cost": br.cost
                }

            for v in responses["voters"]:
                if v["response"]:
                    vr = v["response"]
                    round_data["responses"]["voters"].append({
                        "model": v["model"],
                        "vote": vr.vote.value if vr.vote else None,
                        "vote_reason": vr.vote_reason,
                        "content": vr.content
                    })

            for rv in responses["reviewers"]:
                if rv["response"]:
                    rvr = rv["response"]
                    round_data["responses"]["reviewers"].append({
                        "model": rv["model"],
                        "content": rvr.content
                    })

            rounds_data.append(round_data)

        return {
            "exported_at": datetime.utcnow().isoformat(),
            "session": {
                "id": session.id,
                "name": session.name,
                "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
                "execution_mode": session.execution_mode,
                "voting_threshold": session.voting_threshold,
                "master_prompt": session.master_prompt,
                "master_guardrails": session.master_guardrails,
                "created_at": session.created_at.isoformat() if session.created_at else None,
            },
            "rounds": rounds_data,
            "stats": stats
        }

    # =========================================================================
    # Phase 2: Memory System Integration
    # =========================================================================

    def get_memory_status(self) -> Dict[str, Any]:
        """
        Get current status of the Memory System integration.

        Returns:
            Dictionary with memory system status:
            {
                "enabled": bool,
                "rag_available": bool,
                "context_assembler_available": bool,
                "rag_stats": dict (if RAG available),
                "context_health": dict (if assembler available)
            }
        """
        status = {
            "enabled": self.memory_enabled,
            "rag_available": self.rag_service is not None,
            "context_assembler_available": self.context_assembler is not None,
            "rag_stats": None,
            "context_health": None
        }

        if self.rag_service:
            try:
                status["rag_stats"] = self.rag_service.get_stats()
            except Exception:
                status["rag_stats"] = {"error": "Failed to get stats"}

        if self.context_assembler:
            try:
                # Estimate current token usage (rough estimate)
                current_tokens = 0  # Could be calculated from session
                status["context_health"] = self.context_assembler.get_context_health(current_tokens)
            except Exception:
                status["context_health"] = {"error": "Failed to get health"}

        return status

    def store_manual_decision(
        self,
        decision: str,
        context: str = None,
        project_id: int = None
    ) -> bool:
        """
        Manually store a decision in RAG (for non-roundtable decisions).

        Args:
            decision: The decision text
            context: Additional context
            project_id: Optional project ID

        Returns:
            True if stored successfully
        """
        if not self.memory_enabled or not self.rag_service:
            return False

        try:
            self.rag_service.store_decision(
                decision=decision,
                context=context,
                project_id=project_id
            )
            return True
        except Exception:
            return False


# =============================================================================
# Phase G: Prompt Presets
# =============================================================================

PROMPT_PRESETS = {
    "coding": {
        "name": "Coding",
        "system": "You are an expert software developer. Write clean, well-documented code following best practices.",
        "guardrails": "Always include error handling. Follow PEP8 for Python. Add type hints. Write docstrings for functions."
    },
    "review": {
        "name": "Code Review",
        "system": "You are a senior code reviewer. Analyze code for issues, improvements, and best practices.",
        "guardrails": "Check for security issues, performance problems, code smells. Suggest specific improvements with examples."
    },
    "refactor": {
        "name": "Refactoring",
        "system": "You are a refactoring specialist. Improve code structure without changing behavior.",
        "guardrails": "Maintain backward compatibility. Keep functions small and focused. Improve naming. Add tests if missing."
    },
    "debug": {
        "name": "Debugging",
        "system": "You are a debugging expert. Analyze code to find and fix bugs systematically.",
        "guardrails": "Identify root cause before fixing. Explain the bug clearly. Provide test cases to verify the fix."
    },
    "architect": {
        "name": "Architecture",
        "system": "You are a software architect. Design scalable, maintainable system architectures.",
        "guardrails": "Consider scalability, security, and maintainability. Document trade-offs. Follow SOLID principles."
    }
}


# =============================================================================
# Phase J: Testing System
# =============================================================================

class TestRunner:
    """Test runner for validating code output from roundtable sessions."""

    def run_tier1(self, code: str) -> Dict[str, Any]:
        """
        Tier 1: Syntax and compile checks.

        Args:
            code: Python code to check

        Returns:
            Dictionary with test results
        """
        results = {
            "tier": 1,
            "name": "Syntax Check",
            "passed": True,
            "errors": []
        }

        if not code or not code.strip():
            results["passed"] = False
            results["errors"].append("No code provided")
            return results

        # Extract Python code blocks if markdown
        code_to_check = code
        if "```python" in code:
            import re
            python_blocks = re.findall(r'```python\n(.*?)```', code, re.DOTALL)
            if python_blocks:
                code_to_check = "\n\n".join(python_blocks)
        elif "```" in code:
            import re
            code_blocks = re.findall(r'```\n?(.*?)```', code, re.DOTALL)
            if code_blocks:
                code_to_check = "\n\n".join(code_blocks)

        # Syntax check
        try:
            compile(code_to_check, "<string>", "exec")
        except SyntaxError as e:
            results["passed"] = False
            results["errors"].append(f"Syntax error at line {e.lineno}: {e.msg}")

        return results

    def run_tier2(self) -> Dict[str, Any]:
        """
        Tier 2: App start test - verify the main app can be imported.

        Returns:
            Dictionary with test results
        """
        results = {
            "tier": 2,
            "name": "App Import Check",
            "passed": True,
            "errors": []
        }

        try:
            import subprocess
            result = subprocess.run(
                ["python", "-c", "from app.streamlit_app import main"],
                capture_output=True,
                timeout=30,
                cwd="/home/user/design-tree-studio"
            )
            if result.returncode != 0:
                results["passed"] = False
                error_msg = result.stderr.decode()[:500] if result.stderr else "Unknown error"
                results["errors"].append(f"Import failed: {error_msg}")
        except subprocess.TimeoutExpired:
            results["passed"] = False
            results["errors"].append("Import check timed out (30s)")
        except Exception as e:
            results["passed"] = False
            results["errors"].append(f"Test execution error: {str(e)}")

        return results

    def run_tier3_lint(self, code: str) -> Dict[str, Any]:
        """
        Tier 3: Basic linting checks.

        Args:
            code: Python code to lint

        Returns:
            Dictionary with test results
        """
        results = {
            "tier": 3,
            "name": "Lint Check",
            "passed": True,
            "errors": [],
            "warnings": []
        }

        if not code:
            return results

        # Basic checks
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                results["warnings"].append(f"Line {i}: exceeds 120 characters ({len(line)})")

            # Check for common issues
            if "import *" in line:
                results["warnings"].append(f"Line {i}: wildcard import detected")

            if "eval(" in line or "exec(" in line:
                results["warnings"].append(f"Line {i}: potentially unsafe eval/exec usage")

        # Warnings don't fail the test, but multiple warnings is a concern
        if len(results["warnings"]) > 10:
            results["passed"] = False
            results["errors"].append(f"Too many lint warnings ({len(results['warnings'])})")

        return results

    def run_all(self, code: str = None) -> List[Dict[str, Any]]:
        """
        Run all enabled test tiers.

        Args:
            code: Optional code to test (for tier 1 and 3)

        Returns:
            List of test result dictionaries
        """
        results = []

        if code:
            results.append(self.run_tier1(code))
            results.append(self.run_tier3_lint(code))

        results.append(self.run_tier2())

        return results

    def get_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary of test results.

        Args:
            results: List of test results

        Returns:
            Summary dictionary
        """
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        all_errors = []
        all_warnings = []

        for r in results:
            all_errors.extend(r.get("errors", []))
            all_warnings.extend(r.get("warnings", []))

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "all_passed": failed == 0,
            "errors": all_errors,
            "warnings": all_warnings
        }
