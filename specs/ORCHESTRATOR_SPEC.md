# Orchestrator Specification

**Version:** 1.0
**Priority:** HIGH - Build after Memory System
**Purpose:** 3-tier agent control with natural language + manual controls

---

## Overview

The Orchestrator provides intelligent control over the Round Table through three tiers:

1. **Elders** - Strategic oversight (expensive models, called sparingly)
2. **Conductor** - Mechanical operations (cheap model, called frequently)
3. **Workers** - Task execution (Round Table agents)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              YOU                                     │
│                     (Natural Language Commands)                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TIER 1: ELDER COUNCIL                            │
│                    (Strategic Oversight)                            │
│                                                                     │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │  Opus 4.5   │  │  GPT-5.2    │  │  Gemini 3   │              │
│     │   (Elder)   │  │   (Elder)   │  │   (Elder)   │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                     │
│     Called: On-demand checkpoints, strategic decisions              │
│     Cost: $$$ per consultation                                      │
│     Count: Even number (2 or 4) if user votes with them            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TIER 2: THE CONDUCTOR                            │
│                    (Mechanical Operations)                          │
│                                                                     │
│                      ┌─────────────────┐                            │
│                      │   Haiku 3.5     │                            │
│                      │  (Conductor)    │                            │
│                      │                 │                            │
│                      │ • Parse intent  │                            │
│                      │ • Fill prompts  │                            │
│                      │ • Switch modes  │                            │
│                      │ • Orchestrate   │                            │
│                      └─────────────────┘                            │
│                                                                     │
│     Called: Every user command                                      │
│     Cost: $ per call (very cheap)                                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TIER 3: WORKERS (Round Table)                    │
│                                                                     │
│   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
│   │  1  │  │  2  │  │  3  │  │  4  │  │  5  │  │  6  │  │  7  │  │
│   └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  │
│                                                                     │
│     Modes: PARALLEL | SEQUENTIAL | HYBRID | DEBATE | CRITIQUE       │
│     Called: As orchestrated by Conductor                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Elder Council Service

### Location
`app/services/elder_service.py` (new file)

### Configuration

```python
# Elder model configuration
ELDER_MODELS = {
    "opus": {
        "name": "Opus 4.5",
        "model_id": "claude-opus-4-5-20250101",
        "provider": "anthropic",
        "cost_per_1k_input": 0.015,
        "cost_per_1k_output": 0.075,
    },
    "gpt5": {
        "name": "GPT-5.2",
        "model_id": "gpt-5.2-2025-12-11",
        "provider": "openai",
        "cost_per_1k_input": 0.00175,
        "cost_per_1k_output": 0.014,
    },
    "gemini": {
        "name": "Gemini 3 Pro",
        "model_id": "gemini-3-pro-preview",
        "provider": "google",
        "cost_per_1k_input": 0.00125,
        "cost_per_1k_output": 0.005,
    },
}
```

### Implementation

```python
# app/services/elder_service.py

from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ElderResponse:
    elder_name: str
    provider: str
    content: str
    tokens_in: int
    tokens_out: int
    cost: float
    timestamp: datetime

class ElderCouncilService:
    """
    Strategic oversight layer - expensive models that observe
    and provide wisdom on the overall process.
    """

    def __init__(
        self,
        anthropic_key: str = None,
        openai_key: str = None,
        google_key: str = None,
        active_elders: List[str] = None
    ):
        """
        Initialize Elder Council.

        Args:
            anthropic_key: API key for Claude
            openai_key: API key for OpenAI
            google_key: API key for Google
            active_elders: List of elder IDs to use (e.g., ["opus", "gpt5"])
        """
        self.keys = {
            "anthropic": anthropic_key,
            "openai": openai_key,
            "google": google_key,
        }

        # Default to 2 elders (even number for tie-breaking with user)
        self.active_elders = active_elders or ["opus", "gpt5"]

        # Initialize clients
        self._init_clients()

        # Observation log (doesn't cost tokens until consulted)
        self.observation_log: List[Dict] = []

    def _init_clients(self):
        """Initialize API clients for active elders."""
        self.clients = {}

        if self.keys["anthropic"]:
            import anthropic
            self.clients["anthropic"] = anthropic.Anthropic(api_key=self.keys["anthropic"])

        if self.keys["openai"]:
            from openai import OpenAI
            self.clients["openai"] = OpenAI(api_key=self.keys["openai"])

        if self.keys["google"]:
            import google.generativeai as genai
            genai.configure(api_key=self.keys["google"])
            self.clients["google"] = genai

    def log_observation(self, event: str, details: str = None):
        """
        Log an event for potential later review by Elders.
        NO API COST - just local storage.

        Args:
            event: Short description of what happened
            details: Optional longer details
        """
        self.observation_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details
        })

        # Keep log manageable (last 100 events)
        if len(self.observation_log) > 100:
            self.observation_log = self.observation_log[-100:]

    def consult(
        self,
        question: str = None,
        include_observations: bool = True,
        custom_context: str = None
    ) -> List[ElderResponse]:
        """
        Consult the Elder Council.
        THIS IS WHEN YOU PAY - only call when needed.

        Args:
            question: Specific question to ask (optional)
            include_observations: Include observation log in context
            custom_context: Additional context to provide

        Returns:
            List of responses from each Elder
        """
        # Build context from observations
        context = ""
        if include_observations and self.observation_log:
            recent = self.observation_log[-20:]  # Last 20 events
            context = "## Recent Events\n"
            for obs in recent:
                context += f"- [{obs['timestamp'][:16]}] {obs['event']}\n"
            context += "\n"

        if custom_context:
            context += f"## Additional Context\n{custom_context}\n\n"

        # Build prompt
        base_prompt = """You are an Elder advisor observing a multi-agent AI coding system.

Your role is to provide strategic insight and wisdom based on what you observe.
Focus on:
- Patterns you notice (good or bad)
- Potential issues before they become problems
- Suggestions for improving the process
- Assessment of progress toward goals

Be concise but insightful. 2-3 paragraphs maximum."""

        full_prompt = base_prompt + "\n\n" + context

        if question:
            full_prompt += f"\n## Specific Question\n{question}\n"
        else:
            full_prompt += "\n## Your Task\nProvide your observations and any concerns or suggestions.\n"

        # Query each active Elder
        responses = []
        for elder_id in self.active_elders:
            if elder_id not in ELDER_MODELS:
                continue

            elder_config = ELDER_MODELS[elder_id]
            response = self._call_elder(elder_config, full_prompt)
            if response:
                responses.append(response)

        return responses

    def _call_elder(self, elder_config: Dict, prompt: str) -> Optional[ElderResponse]:
        """Call a single Elder and return response."""
        provider = elder_config["provider"]
        model_id = elder_config["model_id"]

        try:
            if provider == "anthropic" and "anthropic" in self.clients:
                response = self.clients["anthropic"].messages.create(
                    model=model_id,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
                tokens_in = response.usage.input_tokens
                tokens_out = response.usage.output_tokens

            elif provider == "openai" and "openai" in self.clients:
                response = self.clients["openai"].chat.completions.create(
                    model=model_id,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.choices[0].message.content
                tokens_in = response.usage.prompt_tokens
                tokens_out = response.usage.completion_tokens

            elif provider == "google" and "google" in self.clients:
                model = self.clients["google"].GenerativeModel(model_id)
                response = model.generate_content(prompt)
                content = response.text
                tokens_in = len(prompt) // 4  # Estimate
                tokens_out = len(content) // 4

            else:
                return None

            # Calculate cost
            cost = (
                (tokens_in / 1000) * elder_config["cost_per_1k_input"] +
                (tokens_out / 1000) * elder_config["cost_per_1k_output"]
            )

            return ElderResponse(
                elder_name=elder_config["name"],
                provider=provider,
                content=content,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                timestamp=datetime.now()
            )

        except Exception as e:
            print(f"Error calling Elder {elder_config['name']}: {e}")
            return None

    def get_consensus(self, responses: List[ElderResponse]) -> Dict:
        """
        Analyze Elder responses for consensus.

        Returns:
            Dict with consensus analysis
        """
        if not responses:
            return {"consensus": "none", "summary": "No Elder responses"}

        # Simple analysis - could be enhanced with LLM
        contents = [r.content for r in responses]

        return {
            "elder_count": len(responses),
            "total_cost": sum(r.cost for r in responses),
            "responses": [
                {"elder": r.elder_name, "content": r.content}
                for r in responses
            ]
        }

    def set_active_elders(self, elder_ids: List[str]):
        """Change which Elders are active."""
        valid_ids = [e for e in elder_ids if e in ELDER_MODELS]
        if valid_ids:
            self.active_elders = valid_ids

    def clear_observations(self):
        """Clear the observation log."""
        self.observation_log = []
```

---

## Component 2: Conductor Service

### Location
`app/services/conductor_service.py` (new file)

### Model Choice

**Use Haiku 3.5** for the Conductor:
- Very fast (~0.5s response)
- Very cheap (~$0.001 per call)
- Good enough for parsing intent and filling prompts
- NOT for deep reasoning (that's what Elders are for)

### Implementation

```python
# app/services/conductor_service.py

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class ConductorAction:
    action_type: str      # "set_prompt", "set_mode", "execute", etc.
    target: Any           # Agent ID, mode name, etc.
    parameters: Dict      # Additional parameters
    confirmation: str     # Human-readable description

class ConductorService:
    """
    The mechanical operator - interprets natural language commands
    and manipulates the Round Table configuration.

    Uses a cheap, fast model (Haiku) for parsing and orchestration.
    """

    # Available tools the Conductor can use
    TOOLS = [
        {
            "name": "set_agent_prompt",
            "description": "Set or update the prompt for a specific agent",
            "parameters": {
                "agent_id": "int - The agent number (1-7)",
                "prompt": "str - The new prompt"
            }
        },
        {
            "name": "set_group_prompt",
            "description": "Set the same prompt for multiple agents",
            "parameters": {
                "agent_ids": "list[int] - List of agent numbers",
                "prompt": "str - The prompt to apply to all"
            }
        },
        {
            "name": "set_execution_mode",
            "description": "Change how agents execute",
            "parameters": {
                "mode": "str - One of: parallel, sequential, hybrid, debate, critique"
            }
        },
        {
            "name": "assign_role",
            "description": "Assign a role to an agent",
            "parameters": {
                "agent_id": "int - The agent number",
                "role": "str - One of: brainstormer, builder, critic, voter, defender, attacker, judge"
            }
        },
        {
            "name": "execute_round",
            "description": "Execute the current round with configured agents",
            "parameters": {}
        },
        {
            "name": "add_agent",
            "description": "Add a new agent to the round table",
            "parameters": {
                "model_name": "str - Model to use (e.g., 'Opus 4.5', 'GPT-5.2')"
            }
        },
        {
            "name": "remove_agent",
            "description": "Remove an agent from the round table",
            "parameters": {
                "agent_id": "int - The agent number to remove"
            }
        },
        {
            "name": "show_status",
            "description": "Show current round table configuration",
            "parameters": {}
        },
        {
            "name": "consult_elders",
            "description": "Ask the Elder Council for strategic input",
            "parameters": {
                "question": "str - Optional specific question"
            }
        },
    ]

    # Role templates for quick assignment
    ROLE_TEMPLATES = {
        "brainstormer": "Generate creative ideas and approaches. Think broadly.",
        "builder": "Write clean, production-ready code. Follow best practices.",
        "critic": "Find issues, weaknesses, and potential problems. Be thorough.",
        "voter": "Review and vote APPROVE or REJECT with clear reasoning.",
        "defender": "Defend the current approach. Argue for its strengths.",
        "attacker": "Challenge the approach. Find weaknesses and alternatives.",
        "judge": "Evaluate all perspectives and determine the best path forward.",
        "skeptic": "Question assumptions. Play devil's advocate.",
        "optimizer": "Focus on performance, efficiency, and improvements.",
        "security": "Focus on security vulnerabilities and best practices.",
    }

    def __init__(
        self,
        anthropic_key: str,
        roundtable_service,
        elder_service = None
    ):
        """
        Initialize Conductor.

        Args:
            anthropic_key: API key for Haiku
            roundtable_service: Reference to RoundtableService
            elder_service: Optional reference to ElderCouncilService
        """
        import anthropic
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.rt = roundtable_service
        self.elders = elder_service

        # Current session state (for context)
        self.current_session_id = None
        self.current_round_id = None

    def process_command(
        self,
        user_input: str,
        session_context: Dict = None
    ) -> Dict:
        """
        Process a natural language command from the user.

        Args:
            user_input: What the user said
            session_context: Current state information

        Returns:
            Dict with actions taken and results
        """
        # Build prompt for Haiku
        system_prompt = self._build_system_prompt(session_context)
        user_prompt = f"""User command: {user_input}

Analyze this command and determine what actions to take.
Return a JSON array of actions. Each action should have:
- action_type: The tool to use
- target: What to apply it to
- parameters: The parameters needed
- confirmation: A human-readable description

Example response:
```json
[
  {{"action_type": "set_group_prompt", "target": [1, 2], "parameters": {{"prompt": "Brainstorm ideas for auth"}}, "confirmation": "Set agents 1 and 2 to brainstorm authentication ideas"}},
  {{"action_type": "set_execution_mode", "target": "parallel", "parameters": {{}}, "confirmation": "Set mode to parallel execution"}}
]
```

If the command is unclear, return a single action of type "clarify" with a question.
"""

        # Call Haiku (fast & cheap)
        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse response
        actions = self._parse_actions(response.content[0].text)

        # Execute actions
        results = self._execute_actions(actions)

        return {
            "success": True,
            "actions": actions,
            "results": results,
            "confirmation": self._build_confirmation(actions)
        }

    def _build_system_prompt(self, context: Dict = None) -> str:
        """Build system prompt with current state."""
        prompt = """You are the Conductor of a multi-agent AI system called the Round Table.

Your job is to interpret user commands and convert them into specific actions.
You control:
- Agent prompts (what each agent is told to do)
- Execution mode (parallel, sequential, hybrid, debate, critique)
- Agent roles (brainstormer, builder, critic, voter, etc.)
- Round execution

Available tools:
"""
        for tool in self.TOOLS:
            prompt += f"\n- {tool['name']}: {tool['description']}"

        prompt += f"""

Available roles and their templates:
"""
        for role, template in self.ROLE_TEMPLATES.items():
            prompt += f"\n- {role}: {template[:50]}..."

        if context:
            prompt += f"""

Current State:
- Active agents: {context.get('agent_count', 'unknown')}
- Current mode: {context.get('mode', 'unknown')}
- Current round: {context.get('round', 'unknown')}
"""

        return prompt

    def _parse_actions(self, response_text: str) -> List[ConductorAction]:
        """Parse Haiku's response into actions."""
        # Extract JSON from response
        try:
            # Find JSON block
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            actions_data = json.loads(json_str.strip())

            return [
                ConductorAction(
                    action_type=a.get("action_type"),
                    target=a.get("target"),
                    parameters=a.get("parameters", {}),
                    confirmation=a.get("confirmation", "")
                )
                for a in actions_data
            ]

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            # If parsing fails, return clarification request
            return [ConductorAction(
                action_type="error",
                target=None,
                parameters={"error": str(e)},
                confirmation="Failed to parse command. Please try rephrasing."
            )]

    def _execute_actions(self, actions: List[ConductorAction]) -> List[Dict]:
        """Execute parsed actions against the Round Table."""
        results = []

        for action in actions:
            result = {"action": action.action_type, "success": False}

            try:
                if action.action_type == "set_agent_prompt":
                    self.rt.update_agent(
                        action.target,
                        prompt_override=action.parameters["prompt"]
                    )
                    result["success"] = True

                elif action.action_type == "set_group_prompt":
                    for agent_id in action.target:
                        self.rt.update_agent(
                            agent_id,
                            prompt_override=action.parameters["prompt"]
                        )
                    result["success"] = True

                elif action.action_type == "set_execution_mode":
                    if self.current_session_id:
                        self.rt.update_session(
                            self.current_session_id,
                            execution_mode=action.target
                        )
                        result["success"] = True

                elif action.action_type == "assign_role":
                    role = action.parameters.get("role")
                    if role in self.ROLE_TEMPLATES:
                        self.rt.update_agent(
                            action.target,
                            role=role,
                            prompt_override=self.ROLE_TEMPLATES[role]
                        )
                        result["success"] = True

                elif action.action_type == "execute_round":
                    if self.current_round_id:
                        exec_result = self.rt.execute_round(self.current_round_id)
                        result["success"] = exec_result.get("success", False)
                        result["execution_result"] = exec_result

                elif action.action_type == "consult_elders":
                    if self.elders:
                        responses = self.elders.consult(
                            question=action.parameters.get("question")
                        )
                        result["success"] = True
                        result["elder_responses"] = responses

                elif action.action_type == "clarify":
                    result["success"] = True
                    result["needs_clarification"] = True

                elif action.action_type == "error":
                    result["error"] = action.parameters.get("error")

            except Exception as e:
                result["error"] = str(e)

            results.append(result)

        return results

    def _build_confirmation(self, actions: List[ConductorAction]) -> str:
        """Build human-readable confirmation of actions."""
        if not actions:
            return "No actions taken."

        confirmations = [a.confirmation for a in actions if a.confirmation]
        return "\n".join(f"✓ {c}" for c in confirmations)

    def quick_action(self, action_type: str, **kwargs) -> Dict:
        """
        Execute a quick action without natural language parsing.
        For button-based UI.
        """
        action = ConductorAction(
            action_type=action_type,
            target=kwargs.get("target"),
            parameters=kwargs,
            confirmation=""
        )
        results = self._execute_actions([action])
        return results[0] if results else {"success": False}
```

---

## Component 3: Execution Modes

### Add to Round Table Service

```python
# Add to app/services/roundtable_service.py

EXECUTION_MODES = {
    "sequential": "Agents execute one after another (builder → voters)",
    "parallel": "All agents answer the same prompt simultaneously",
    "hybrid": "Groups execute in sequence, within groups in parallel",
    "debate": "Two sides argue, others judge",
    "critique": "All agents critique each other's responses",
}

def execute_parallel(
    self,
    round_id: int,
    prompt: str
) -> List[RoundtableResponse]:
    """
    Execute all agents with the same prompt in parallel (conceptually).

    All agents receive the same prompt and respond independently.
    No builder/voter distinction - everyone is equal contributor.
    """
    round_obj = self.get_round(round_id)
    if not round_obj:
        return []

    session = round_obj.session
    system_prompt = session.master_prompt or DEFAULT_SYSTEM_PROMPT

    responses = []
    for agent in round_obj.agents:
        # All agents get the same prompt
        response = self.call_agent(
            agent=agent,
            system_prompt=system_prompt,
            user_prompt=prompt
        )
        responses.append(response)

    return responses

def execute_critique(
    self,
    round_id: int,
    responses_to_critique: List[RoundtableResponse]
) -> List[RoundtableResponse]:
    """
    Have all agents critique a set of responses.

    Each agent sees all previous responses and provides analysis.
    """
    round_obj = self.get_round(round_id)
    if not round_obj:
        return []

    session = round_obj.session
    system_prompt = session.master_prompt or DEFAULT_SYSTEM_PROMPT

    # Format all responses for review
    all_responses_text = "\n\n".join([
        f"## Response {i+1}\n{r.content}"
        for i, r in enumerate(responses_to_critique)
    ])

    critique_prompt = f"""Review and critique the following responses:

{all_responses_text}

For each response:
1. Identify strengths
2. Identify weaknesses
3. Rate quality (1-10)
4. Suggest improvements

Then provide your overall ranking of which response is best and why."""

    critiques = []
    for agent in round_obj.agents:
        critique = self.call_agent(
            agent=agent,
            system_prompt=system_prompt,
            user_prompt=critique_prompt
        )
        critiques.append(critique)

    return critiques

def execute_debate(
    self,
    round_id: int,
    topic: str,
    defender_ids: List[int],
    attacker_ids: List[int],
    judge_ids: List[int]
) -> Dict:
    """
    Execute a structured debate between agents.

    Args:
        topic: What to debate
        defender_ids: Agents defending the current approach
        attacker_ids: Agents attacking/challenging
        judge_ids: Agents who will judge the debate

    Returns:
        Dict with debate results and verdict
    """
    round_obj = self.get_round(round_id)
    session = round_obj.session
    system_prompt = session.master_prompt or DEFAULT_SYSTEM_PROMPT

    results = {
        "topic": topic,
        "defender_arguments": [],
        "attacker_arguments": [],
        "verdicts": []
    }

    # Defenders make their case
    for agent_id in defender_ids:
        agent = self.get_agent(agent_id)
        if agent:
            response = self.call_agent(
                agent=agent,
                system_prompt=system_prompt + "\n\nYou are DEFENDING this approach.",
                user_prompt=f"Defend this approach: {topic}\n\nMake your strongest case."
            )
            results["defender_arguments"].append(response)

    # Attackers respond
    defender_args = "\n\n".join([r.content for r in results["defender_arguments"]])
    for agent_id in attacker_ids:
        agent = self.get_agent(agent_id)
        if agent:
            response = self.call_agent(
                agent=agent,
                system_prompt=system_prompt + "\n\nYou are ATTACKING this approach.",
                user_prompt=f"""Topic: {topic}

Defender arguments:
{defender_args}

Counter these arguments. Find weaknesses. Propose alternatives."""
            )
            results["attacker_arguments"].append(response)

    # Judges render verdict
    attacker_args = "\n\n".join([r.content for r in results["attacker_arguments"]])
    for agent_id in judge_ids:
        agent = self.get_agent(agent_id)
        if agent:
            response = self.call_agent(
                agent=agent,
                system_prompt=system_prompt + "\n\nYou are the JUDGE.",
                user_prompt=f"""Topic: {topic}

DEFENSE:
{defender_args}

ATTACK:
{attacker_args}

Render your verdict. Who made the stronger case? What should we do?"""
            )
            results["verdicts"].append(response)

    return results
```

---

## UI Integration

### Dual Control Interface

```python
# Add to app/ui/roundtable_panel.py

def render_orchestrator_panel(conductor: ConductorService, elders: ElderCouncilService):
    """Render the Orchestrator control panel with both chat and buttons."""

    st.header("🎼 Orchestrator Control")

    # Tab selection: Chat vs Manual
    tab1, tab2 = st.tabs(["💬 Natural Language", "🔘 Manual Controls"])

    with tab1:
        # Chat interface with Conductor
        st.subheader("Talk to the Conductor")

        user_command = st.text_area(
            "Your command:",
            placeholder="e.g., 'Have agents 1-3 brainstorm, 4-5 critique'",
            height=100
        )

        if st.button("Send Command"):
            if user_command:
                with st.spinner("Conductor processing..."):
                    result = conductor.process_command(user_command)

                st.success(result["confirmation"])

                if any(r.get("execution_result") for r in result["results"]):
                    st.subheader("Execution Results")
                    # Display results...

    with tab2:
        # Manual button controls
        st.subheader("Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**Execution Mode**")
            mode = st.selectbox("Mode", list(EXECUTION_MODES.keys()))
            if st.button("Set Mode"):
                conductor.quick_action("set_execution_mode", target=mode)
                st.success(f"Mode set to {mode}")

        with col2:
            st.write("**Quick Execute**")
            if st.button("▶ Execute Round"):
                result = conductor.quick_action("execute_round")
                st.success("Round executed")

            if st.button("⏸ Pause"):
                st.info("Paused")

        with col3:
            st.write("**Elders**")
            if st.button("👁 Consult Elders"):
                result = conductor.quick_action("consult_elders")
                if result.get("elder_responses"):
                    for er in result["elder_responses"]:
                        st.info(f"**{er.elder_name}**: {er.content[:200]}...")

        # Agent Grid
        st.subheader("Agent Configuration")

        # Get current agents
        # Display in editable grid...
```

---

## Cost Tracking

### Add to Both Services

```python
class CostTracker:
    """Track costs across all tiers."""

    def __init__(self):
        self.costs = {
            "conductor": 0.0,
            "elders": 0.0,
            "workers": 0.0,
        }
        self.calls = {
            "conductor": 0,
            "elders": 0,
            "workers": 0,
        }

    def add_cost(self, tier: str, amount: float):
        self.costs[tier] = self.costs.get(tier, 0) + amount
        self.calls[tier] = self.calls.get(tier, 0) + 1

    def get_total(self) -> float:
        return sum(self.costs.values())

    def get_breakdown(self) -> Dict:
        return {
            "costs": self.costs,
            "calls": self.calls,
            "total": self.get_total()
        }

    def reset(self):
        self.costs = {k: 0.0 for k in self.costs}
        self.calls = {k: 0 for k in self.calls}
```

---

## File Structure

```
app/
├── services/
│   ├── elder_service.py       # NEW
│   ├── conductor_service.py   # NEW
│   ├── cost_tracker.py        # NEW
│   └── roundtable_service.py  # MODIFY - add execution modes
└── ui/
    └── roundtable_panel.py    # MODIFY - add orchestrator UI
```

---

## Success Criteria

The Orchestrator is complete when:

1. **Natural Language**: User can type commands, Conductor executes them
2. **Manual Controls**: Buttons and dropdowns work for all operations
3. **Elders**: Can be consulted on-demand, provide strategic insight
4. **Modes**: Parallel, sequential, hybrid, debate, critique all work
5. **Cost Tracking**: Real-time visibility into spending
6. **Flexible**: Can switch between any mode at any time

---

*Build this after Memory System. Together they form the control layer.*
