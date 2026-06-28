"""Deterministic Context Builder for Agent Runtime."""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Constructs the LLM context deterministically:
    1. Workspace Policies
    2. System Prompt
    3. Agent Prompt
    4. Conversation Context
    5. Workspace Memory
    6. Agent Memory
    7. Conversation Memory
    8. Knowledge Retrieval
    9. Tool Availability
    10. Workflow Availability
    11. Model Configuration
    12. LLM Request
    """

    def __init__(self):
        pass
        
    async def build_messages(
        self,
        workspace_policies: str,
        system_prompt: str,
        agent_prompt: str,
        conversation_context: str,
        workspace_memory: str,
        agent_memory: str,
        conversation_memory: str,
        knowledge_retrieval: str,
        tool_availability: str,
        workflow_availability: str,
        model_configuration: str,
        conversation_history: List[Dict[str, Any]],
        user_message: str
    ) -> List[Dict[str, Any]]:
        """
        Builds the unified list of messages to send to the LLM.
        Workspace policies are strictly unbypassable and applied first.
        """
        messages = []
        
        # Assemble the deterministic system content block
        system_content = f"""[WORKSPACE POLICIES - STRICTLY ENFORCED]
{workspace_policies or 'None'}

[SYSTEM INSTRUCTIONS]
{system_prompt or 'None'}

[AGENT ROLE AND OBJECTIVES]
{agent_prompt or 'None'}

[CONVERSATION CONTEXT]
{conversation_context or 'None'}

[WORKSPACE MEMORY]
{workspace_memory or 'None'}

[AGENT MEMORY]
{agent_memory or 'None'}

[CONVERSATION MEMORY]
{conversation_memory or 'None'}

[KNOWLEDGE RETRIEVAL]
{knowledge_retrieval or 'None'}

[TOOL AVAILABILITY]
{tool_availability or 'None'}

[WORKFLOW AVAILABILITY]
{workflow_availability or 'None'}

[MODEL CONFIGURATION]
{model_configuration or 'None'}"""

        messages.append({"role": "system", "content": system_content.strip()})
        
        # Append conversation history
        for msg in conversation_history:
            messages.append(msg)
            
        # Append the final LLM Request
        messages.append({"role": "user", "content": user_message})
            
        return messages
