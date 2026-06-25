from typing import Optional
from backend.app.models.agent import Agent

class ReasoningLayer:
    """
    Model router that decides whether to use Fast, Reasoning, or Vision models 
    based on agent configuration and request capabilities.
    """

    @staticmethod
    def select_model(agent: Agent, requires_vision: bool = False, requires_deep_reasoning: bool = False) -> str:
        """
        Selects the appropriate model ID.
        
        Args:
            agent: The Agent instance containing model configurations.
            requires_vision: Whether the input contains images.
            requires_deep_reasoning: Whether the task explicitly demands slow/deep reasoning.
            
        Returns:
            The model string identifier to pass to the provider.
        """
        # We assume the agent has relationships to active AgentModel configs,
        # or we rely on system defaults if none provided.
        # In this implementation, we map capabilities to standard names.
        
        # If the user explicitly passed capabilities that override standard config:
        if requires_vision:
            return "gemini-2.0-flash" # Gemini Flash handles vision well natively
            
        if requires_deep_reasoning:
            return "gemini-2.0-pro-exp" # Example reasoning model
            
        # Default to the agent's configured model if available, else standard fast model
        return "gemini-2.0-flash"
