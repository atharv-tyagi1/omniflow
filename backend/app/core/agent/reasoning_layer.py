"""Reasoning Layer — configuration-driven model routing for the Agent Runtime."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Model capability tiers — entirely configuration-driven
_PROVIDER_MODEL_TIERS: Dict[str, Dict[str, str]] = {
    "gemini": {
        "fast": "gemini-2.0-flash",
        "reasoning": "gemini-2.5-pro",
        "vision": "gemini-2.0-flash",
        "coding": "gemini-2.5-pro",
        "default": "gemini-2.0-flash",
    },
    "openai": {
        "fast": "gpt-4o-mini",
        "reasoning": "o3",
        "vision": "gpt-4o",
        "coding": "gpt-4o",
        "default": "gpt-4o",
    },
    "anthropic": {
        "fast": "claude-haiku-4-5",
        "reasoning": "claude-opus-4-5",
        "vision": "claude-sonnet-4-5",
        "coding": "claude-sonnet-4-5",
        "default": "claude-sonnet-4-5",
    },
    "openrouter": {
        "fast": "google/gemini-flash-1.5",
        "reasoning": "anthropic/claude-opus-4",
        "vision": "openai/gpt-4o",
        "coding": "openai/gpt-4o",
        "default": "google/gemini-flash-1.5",
    },
}


class ReasoningLayer:
    """
    Routes each request to the optimal model based on:
    1. The agent's configured model (explicit override)
    2. The task_type hint (general, reasoning, vision, coding, fast)
    3. Provider tier defaults

    No model is hardcoded. All routing is configuration-driven.
    Future routing (context length, cost budget) can be added without
    changing the AgentRuntime interface.
    """

    @classmethod
    def select_model(
        cls,
        agent_config: Dict[str, Any],
        task_type: str = "general",
    ) -> str:
        """
        Selects the most appropriate model for the given task.

        Priority:
        1. Explicit model in agent_config (operator override)
        2. Tier-based routing by task_type
        3. Provider default
        4. Global fallback
        """
        provider = agent_config.get("provider", "gemini").lower()
        configured_model = agent_config.get("model", "").strip()

        # 1. Explicit model configured — always respect operator choice
        if configured_model:
            logger.debug(
                f"Using operator-configured model: {provider}/{configured_model}"
            )
            return configured_model

        # 2. Tier-based routing
        provider_tiers = _PROVIDER_MODEL_TIERS.get(provider, _PROVIDER_MODEL_TIERS["gemini"])

        # Normalize task_type
        normalized_task = task_type.lower().replace("-", "_")

        if normalized_task in ("complex_reasoning", "analysis", "reasoning"):
            tier = "reasoning"
        elif normalized_task in ("vision", "image", "multimodal"):
            tier = "vision"
        elif normalized_task in ("code", "coding", "programming", "debug"):
            tier = "coding"
        elif normalized_task in ("fast", "simple", "quick", "chat"):
            tier = "fast"
        else:
            tier = "default"

        selected = provider_tiers.get(tier, provider_tiers["default"])
        logger.info(
            f"Reasoning Layer selected: provider={provider} tier={tier} model={selected} "
            f"(task_type={task_type})"
        )
        return selected

    @classmethod
    def estimate_task_type(cls, user_message: str, tools_requested: bool = False) -> str:
        """
        Heuristically estimates the appropriate task tier from the user message.
        This is a lightweight signal — it does NOT call the LLM.
        Operators can override via agent_config.model.
        """
        msg_lower = user_message.lower()

        # Vision signals
        if any(kw in msg_lower for kw in ("image", "photo", "screenshot", "picture", "chart")):
            return "vision"

        # Coding signals
        if any(kw in msg_lower for kw in (
            "code", "debug", "function", "python", "sql", "script", "implement"
        )):
            return "coding"

        # Complex reasoning signals
        if any(kw in msg_lower for kw in (
            "analyze", "explain why", "compare", "evaluate", "strategy",
            "summarize", "breakdown", "reasoning"
        )):
            return "reasoning"

        # Default to fast for conversational turns
        return "fast"
