from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.agent.prompt_engine import PromptEngine
from backend.app.core.agent.memory_engine import MemoryEngine
from backend.app.core.agent.knowledge_engine import KnowledgeEngine
from backend.app.models.agent_version import AgentVersion

class ContextBuilder:
    """
    Constructs the LLM context deterministically: 
    Workspace Policies -> System Prompt -> Agent Prompt -> Conversation Context -> 
    Workspace Memory -> Agent Memory -> Conversation Memory -> Knowledge Retrieval -> 
    Tool Availability -> Workflow Availability -> Model Configuration -> LLM Request.
    """

    @staticmethod
    async def build_context(
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        agent_version: AgentVersion,
        conversation_id: UUID,
        query: str,
        workspace_policies: List[str],
        available_tools: List[str],
        available_workflows: List[str],
        model_config: Dict[str, Any]
    ) -> str:
        """
        Builds the complete formatted context string for the LLM.
        """
        parts = []

        # 1. Workspace Policies (unbypassable and applied first)
        if workspace_policies:
            parts.append("## WORKSPACE POLICIES (MANDATORY)\n" + "\n".join(workspace_policies))

        # 2. System Prompt
        system_prompt = PromptEngine.get_active_prompt(agent_version)
        parts.append(f"## SYSTEM PROMPT\n{system_prompt}")

        # 3. Agent Prompt (Task/Role specifics)
        # Using the base query or additional agent instruction set
        parts.append(f"## AGENT PROMPT / CURRENT QUERY\n{query}")

        # 4. Conversation Context (History)
        # We assume conversation context is injected later or retrieved here
        parts.append("## CONVERSATION CONTEXT\n[History injected here]")

        # 5-7. Memories
        memories = await MemoryEngine.assemble_memory_context(db, workspace_id, agent_id, conversation_id)
        parts.append(f"## WORKSPACE MEMORY\n{memories['workspace_memory']}")
        parts.append(f"## AGENT MEMORY\n{memories['agent_memory']}")
        parts.append(f"## CONVERSATION MEMORY\n{memories['conversation_memory']}")

        # 8. Knowledge Retrieval (RAG)
        rag_context = await KnowledgeEngine.retrieve_knowledge(db, workspace_id, query)
        parts.append(f"## KNOWLEDGE RETRIEVAL\n{rag_context['context_string']}")

        # 9. Tool Availability
        parts.append(f"## TOOL AVAILABILITY\n{', '.join(available_tools)}")

        # 10. Workflow Availability
        parts.append(f"## WORKFLOW AVAILABILITY\n{', '.join(available_workflows)}")

        # 11. Model Configuration
        # Not explicitly put into text unless instructing the model on its limits
        parts.append(f"## MODEL CONFIGURATION\nModel params restricted by system.")

        return "\n\n".join(parts)
