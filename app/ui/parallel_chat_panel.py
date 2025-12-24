"""
Parallel Multi-Agent Chat Panel.

Enables querying multiple AI models simultaneously for comparison,
consensus building, and model behavior research.

Features:
- 1-20 parallel agents
- Model selection per agent
- Presets for common model combinations
- Side-by-side response display
- Cross-agent judgment/consensus
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from app.services.roundtable_service import AVAILABLE_MODELS
from app.services import get_setting
from app.ui.layout import show_success, show_error, show_warning, show_info


# Default presets for quick model combinations
DEFAULT_PRESETS = {
    "Power Trio": {
        "description": "Top models from each provider",
        "agents": [
            {"model": "Claude Opus 4.5", "label": "Claude"},
            {"model": "GPT-5.2", "label": "GPT"},
            {"model": "Gemini 3 Pro", "label": "Gemini"},
        ]
    },
    "Claude Family": {
        "description": "Compare Claude models",
        "agents": [
            {"model": "Claude Opus 4.5", "label": "Opus 4.5"},
            {"model": "Claude Sonnet 4.5", "label": "Sonnet 4.5"},
            {"model": "Claude Sonnet 3.5", "label": "Sonnet 3.5"},
        ]
    },
    "OpenAI Lineup": {
        "description": "Compare OpenAI models",
        "agents": [
            {"model": "GPT-5.2", "label": "GPT-5.2"},
            {"model": "GPT-4o", "label": "GPT-4o"},
            {"model": "o1", "label": "o1"},
        ]
    },
    "Gemini Variants": {
        "description": "Compare Gemini models",
        "agents": [
            {"model": "Gemini 3 Pro", "label": "Gemini 3"},
            {"model": "Gemini 2.0 Flash Thinking", "label": "Flash Think"},
            {"model": "Gemini 1.5 Pro", "label": "1.5 Pro"},
        ]
    },
    "5x5x5 Research": {
        "description": "5 of each top model (15 total)",
        "agents": [
            {"model": "Claude Opus 4.5", "label": "Claude-1"},
            {"model": "Claude Opus 4.5", "label": "Claude-2"},
            {"model": "Claude Opus 4.5", "label": "Claude-3"},
            {"model": "Claude Opus 4.5", "label": "Claude-4"},
            {"model": "Claude Opus 4.5", "label": "Claude-5"},
            {"model": "GPT-5.2", "label": "GPT-1"},
            {"model": "GPT-5.2", "label": "GPT-2"},
            {"model": "GPT-5.2", "label": "GPT-3"},
            {"model": "GPT-5.2", "label": "GPT-4"},
            {"model": "GPT-5.2", "label": "GPT-5"},
            {"model": "Gemini 3 Pro", "label": "Gem-1"},
            {"model": "Gemini 3 Pro", "label": "Gem-2"},
            {"model": "Gemini 3 Pro", "label": "Gem-3"},
            {"model": "Gemini 3 Pro", "label": "Gem-4"},
            {"model": "Gemini 3 Pro", "label": "Gem-5"},
        ]
    },
    "Variance Test (5x Same)": {
        "description": "5 instances of same model",
        "agents": [
            {"model": "Claude Opus 4.5", "label": "Instance-1"},
            {"model": "Claude Opus 4.5", "label": "Instance-2"},
            {"model": "Claude Opus 4.5", "label": "Instance-3"},
            {"model": "Claude Opus 4.5", "label": "Instance-4"},
            {"model": "Claude Opus 4.5", "label": "Instance-5"},
        ]
    },
    "Deep Variance (10x Same)": {
        "description": "10 instances for personality research",
        "agents": [
            {"model": "Claude Opus 4.5", "label": f"Instance-{i}"} for i in range(1, 11)
        ]
    },
}

# Preset action prompts for cross-agent interaction
ACTION_PRESETS = {
    "Judge Answers": "Review the other agents' responses. Rate each on accuracy, completeness, and clarity (1-10). Identify the best answer and explain why.",
    "Find Consensus": "Analyze all responses and synthesize a consensus answer that combines the best elements from each.",
    "Identify Differences": "Compare all responses and list the key differences in approach, conclusions, or reasoning.",
    "Rate Confidence": "Based on all responses, rate the overall confidence level (1-10) for this answer and explain any areas of uncertainty.",
    "Debate": "Pick the response you most disagree with and provide a counterargument.",
}


def init_parallel_chat_state():
    """Initialize session state for parallel chat."""
    if "parallel_agent_count" not in st.session_state:
        st.session_state.parallel_agent_count = 3
    if "parallel_agents" not in st.session_state:
        st.session_state.parallel_agents = [
            {"model": "Claude Opus 4.5", "label": "Agent 1"},
            {"model": "GPT-5.2", "label": "Agent 2"},
            {"model": "Gemini 3 Pro", "label": "Agent 3"},
        ]
    if "parallel_responses" not in st.session_state:
        st.session_state.parallel_responses = {}
    if "parallel_query" not in st.session_state:
        st.session_state.parallel_query = ""
    if "custom_presets" not in st.session_state:
        st.session_state.custom_presets = {}


def render_parallel_chat_panel(db: Session) -> None:
    """
    Render the parallel multi-agent chat panel.

    Args:
        db: Database session
    """
    init_parallel_chat_state()

    st.markdown("### ⚡ Parallel Multi-Agent Chat")
    st.caption("Query multiple models simultaneously for comparison and research")

    # Get API keys
    anthropic_key = get_setting(db, "ANTHROPIC_API_KEY")
    openai_key = get_setting(db, "OPENAI_API_KEY")
    google_key = get_setting(db, "GOOGLE_API_KEY")

    # Top controls row
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 2])

    with ctrl_col1:
        # Agent count selector (1-20)
        agent_count = st.number_input(
            "Agents",
            min_value=1,
            max_value=20,
            value=st.session_state.parallel_agent_count,
            step=1,
            help="Number of parallel agents (1-20)"
        )
        if agent_count != st.session_state.parallel_agent_count:
            st.session_state.parallel_agent_count = agent_count
            # Adjust agents list
            _adjust_agent_count(agent_count)
            st.rerun()

    with ctrl_col2:
        # Preset selector
        all_presets = {**DEFAULT_PRESETS, **st.session_state.custom_presets}
        preset_names = ["Custom"] + list(all_presets.keys())

        selected_preset = st.selectbox(
            "Preset",
            preset_names,
            index=0,
            help="Quick-load a model combination"
        )

        if selected_preset != "Custom":
            if st.button("Apply Preset", key="apply_preset"):
                preset = all_presets[selected_preset]
                st.session_state.parallel_agents = preset["agents"].copy()
                st.session_state.parallel_agent_count = len(preset["agents"])
                st.rerun()

    with ctrl_col3:
        # Save current as preset
        with st.expander("💾 Save Preset"):
            preset_name = st.text_input("Preset Name", key="new_preset_name")
            preset_desc = st.text_input("Description", key="new_preset_desc")
            if st.button("Save Current Config", key="save_preset"):
                if preset_name:
                    st.session_state.custom_presets[preset_name] = {
                        "description": preset_desc,
                        "agents": st.session_state.parallel_agents.copy()
                    }
                    show_success(f"Saved preset: {preset_name}")

    st.divider()

    # Agent configuration grid
    st.markdown("**Configure Agents:**")

    # Dynamic columns based on agent count
    agents_per_row = min(5, st.session_state.parallel_agent_count)

    for row_start in range(0, st.session_state.parallel_agent_count, agents_per_row):
        row_end = min(row_start + agents_per_row, st.session_state.parallel_agent_count)
        cols = st.columns(row_end - row_start)

        for i, col in enumerate(cols):
            agent_idx = row_start + i
            if agent_idx < len(st.session_state.parallel_agents):
                agent = st.session_state.parallel_agents[agent_idx]

                with col:
                    # Model selector
                    model_names = list(AVAILABLE_MODELS.keys())
                    current_model = agent.get("model", model_names[0])
                    model_idx = model_names.index(current_model) if current_model in model_names else 0

                    new_model = st.selectbox(
                        f"#{agent_idx + 1}",
                        model_names,
                        index=model_idx,
                        key=f"parallel_agent_model_{agent_idx}_{row_start}"
                    )

                    if new_model != current_model:
                        st.session_state.parallel_agents[agent_idx]["model"] = new_model

                    # Label input
                    label = st.text_input(
                        "Label",
                        value=agent.get("label", f"Agent {agent_idx + 1}"),
                        key=f"parallel_agent_label_{agent_idx}_{row_start}",
                        label_visibility="collapsed"
                    )
                    st.session_state.parallel_agents[agent_idx]["label"] = label

    st.divider()

    # Query input
    st.markdown("**Your Query:**")
    query = st.text_area(
        "Query",
        value=st.session_state.parallel_query,
        height=100,
        placeholder="Enter your question here... All agents will answer simultaneously.",
        label_visibility="collapsed",
        key="parallel_query_input"
    )

    # Action buttons row
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 2])

    with btn_col1:
        send_btn = st.button("🚀 Send to All", type="primary", use_container_width=True)

    with btn_col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

    with btn_col3:
        # Action preset dropdown
        action = st.selectbox(
            "Action",
            ["Select Action..."] + list(ACTION_PRESETS.keys()),
            key="action_preset",
            label_visibility="collapsed"
        )

    with btn_col4:
        if action != "Select Action...":
            if st.button(f"▶️ {action}", key="run_action"):
                # Run cross-agent action
                _run_cross_agent_action(db, action, anthropic_key, openai_key, google_key)

    # Handle send
    if send_btn and query.strip():
        st.session_state.parallel_query = query
        _send_to_all_agents(db, query, anthropic_key, openai_key, google_key)

    # Handle clear
    if clear_btn:
        st.session_state.parallel_responses = {}
        st.session_state.parallel_query = ""
        st.rerun()

    st.divider()

    # Response display
    render_parallel_responses()


def _adjust_agent_count(count: int) -> None:
    """Adjust the agents list to match the desired count."""
    current = len(st.session_state.parallel_agents)

    if count > current:
        # Add more agents
        model_names = list(AVAILABLE_MODELS.keys())
        for i in range(current, count):
            # Cycle through available models
            model = model_names[i % len(model_names)]
            st.session_state.parallel_agents.append({
                "model": model,
                "label": f"Agent {i + 1}"
            })
    elif count < current:
        # Remove excess agents
        st.session_state.parallel_agents = st.session_state.parallel_agents[:count]


def _send_to_all_agents(
    db: Session,
    query: str,
    anthropic_key: str,
    openai_key: str,
    google_key: str
) -> None:
    """Send query to all configured agents in parallel."""
    import os

    # Get keys from settings or environment
    anthropic_key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = openai_key or os.environ.get("OPENAI_API_KEY", "")
    google_key = google_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

    responses = {}

    with st.spinner(f"Querying {len(st.session_state.parallel_agents)} agents..."):
        for idx, agent in enumerate(st.session_state.parallel_agents):
            model_name = agent["model"]
            label = agent["label"]
            model_config = AVAILABLE_MODELS.get(model_name, {})
            provider = model_config.get("provider", "")
            model_id = model_config.get("id", "")

            try:
                response = _call_model(
                    provider=provider,
                    model_id=model_id,
                    query=query,
                    anthropic_key=anthropic_key,
                    openai_key=openai_key,
                    google_key=google_key
                )
                responses[idx] = {
                    "label": label,
                    "model": model_name,
                    "response": response,
                    "error": None,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                responses[idx] = {
                    "label": label,
                    "model": model_name,
                    "response": None,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

    st.session_state.parallel_responses = responses
    st.rerun()


def _call_model(
    provider: str,
    model_id: str,
    query: str,
    anthropic_key: str,
    openai_key: str,
    google_key: str
) -> str:
    """Call a specific model and return the response."""

    if provider == "anthropic":
        if not anthropic_key:
            raise ValueError("Anthropic API key not configured")

        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        response = client.messages.create(
            model=model_id,
            max_tokens=4096,
            messages=[{"role": "user", "content": query}]
        )
        return response.content[0].text

    elif provider == "openai":
        if not openai_key:
            raise ValueError("OpenAI API key not configured")

        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": query}],
            max_tokens=4096
        )
        return response.choices[0].message.content

    elif provider == "google":
        if not google_key:
            raise ValueError("Google API key not configured")

        import google.generativeai as genai
        genai.configure(api_key=google_key)
        model = genai.GenerativeModel(model_id)
        response = model.generate_content(query)
        return response.text

    else:
        raise ValueError(f"Unknown provider: {provider}")


def render_parallel_responses() -> None:
    """Render the parallel response boxes."""
    responses = st.session_state.parallel_responses

    if not responses:
        st.info("Send a query to see parallel responses here")
        return

    st.markdown("**Responses:**")

    # Display in grid
    agents_per_row = min(3, len(responses))
    response_list = list(responses.items())

    for row_start in range(0, len(response_list), agents_per_row):
        row_end = min(row_start + agents_per_row, len(response_list))
        cols = st.columns(row_end - row_start)

        for i, col in enumerate(cols):
            idx, data = response_list[row_start + i]

            with col:
                # Header with label and model
                st.markdown(f"**{data['label']}** ({data['model']})")

                if data["error"]:
                    st.error(f"Error: {data['error']}")
                elif data["response"]:
                    # Response in expandable container
                    with st.container():
                        st.markdown(data["response"])
                else:
                    st.warning("No response")

                st.caption(f"📅 {data['timestamp'][:19]}")
                st.divider()


def _run_cross_agent_action(
    db: Session,
    action: str,
    anthropic_key: str,
    openai_key: str,
    google_key: str
) -> None:
    """Run a cross-agent judgment/consensus action."""
    responses = st.session_state.parallel_responses

    if not responses:
        show_warning("No responses to analyze. Send a query first.")
        return

    # Build context from all responses
    context = f"Original Query: {st.session_state.parallel_query}\n\n"
    context += "Agent Responses:\n"
    for idx, data in responses.items():
        context += f"\n--- {data['label']} ({data['model']}) ---\n"
        context += data.get("response", "No response") + "\n"

    # Get action prompt
    action_prompt = ACTION_PRESETS.get(action, "Analyze the responses.")

    full_prompt = f"{context}\n\n{action_prompt}"

    # Use first available model to judge
    with st.spinner(f"Running {action}..."):
        try:
            # Default to Claude for judgment
            if anthropic_key:
                result = _call_model("anthropic", "claude-opus-4-5-20250101", full_prompt, anthropic_key, openai_key, google_key)
            elif openai_key:
                result = _call_model("openai", "gpt-4o", full_prompt, anthropic_key, openai_key, google_key)
            else:
                raise ValueError("No API key available for judgment")

            # Display result
            st.markdown(f"### 🎯 {action} Result")
            st.markdown(result)

        except Exception as e:
            show_error(f"Action failed: {str(e)}")


def render_parallel_chat_compact(db: Session) -> None:
    """
    Render a compact version for embedding in other panels.
    Just the agent count toggle and quick-send.
    """
    init_parallel_chat_state()

    col1, col2 = st.columns([1, 3])

    with col1:
        count = st.number_input(
            "Parallel",
            min_value=1,
            max_value=20,
            value=st.session_state.parallel_agent_count,
            key="compact_parallel_count",
            label_visibility="collapsed"
        )
        if count != st.session_state.parallel_agent_count:
            st.session_state.parallel_agent_count = count
            _adjust_agent_count(count)

    with col2:
        if st.session_state.parallel_agent_count > 1:
            st.caption(f"⚡ {st.session_state.parallel_agent_count} agents will respond")
        else:
            st.caption("Single agent mode")
