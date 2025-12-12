"""
Roundtable Coder service.

Handles session, round, and agent management for the Roundtable Coder feature.
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


# Available models configuration
AVAILABLE_MODELS = {
    # Anthropic
    "Opus 4.5": {
        "id": "claude-opus-4-5-20250101",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    "Sonnet 4.5": {
        "id": "claude-sonnet-4-5-20250929",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    "Sonnet 3.5": {
        "id": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "max_tokens": 200000
    },
    # OpenAI
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
        openai_key: Optional[str] = None
    ):
        """
        Initialize the RoundtableService.

        Args:
            db: SQLAlchemy database session
            anthropic_key: Anthropic API key (optional)
            openai_key: OpenAI API key (optional)
        """
        self.db = db
        self.anthropic_client = None
        self.openai_client = None

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
            # Estimate cost (GPT-4o pricing as baseline)
            cost = (tokens_in * 0.005 / 1000) + (tokens_out * 0.015 / 1000)

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
                "consensus": dict from calculate_consensus()
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
