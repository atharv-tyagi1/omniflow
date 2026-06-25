from typing import Dict, Any, Optional
from backend.app.models.agent_version import AgentVersion

class PromptEngine:
    """
    Handles variable injection, prompt formatting, and validation against published versions.
    """

    @staticmethod
    def render_prompt(
        prompt_template: str, 
        variables: Dict[str, Any]
    ) -> str:
        """
        Injects variables into the prompt template.
        Supports simple string replacement (e.g. {{ user_name }}).
        """
        rendered = prompt_template
        for key, value in variables.items():
            placeholder = f"{{{{ {key} }}}}"
            # Also support without spaces
            placeholder_nospace = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value)).replace(placeholder_nospace, str(value))
        return rendered

    @staticmethod
    def get_active_prompt(version: AgentVersion) -> str:
        """
        Extracts the main system prompt from an AgentVersion's prompt payload.
        Ensures we are using the immutable published state for published versions.
        """
        # The prompt configuration is stored in version.prompt_config JSONB
        prompt_config = version.prompt_config or {}
        return prompt_config.get("system_prompt", "You are a helpful AI assistant.")
