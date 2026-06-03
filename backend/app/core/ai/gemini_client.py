import os
from typing import List
from google import genai
from backend.app.core.config import settings

class GeminiClient:
    """
    Singleton-style wrapper for the modern Google GenAI SDK, enforcing strict 
    model selection and batching for embedding generation.
    """
    _client = None

    SYSTEM_PROMPT = """You are AI Business Analyst, an expert business intelligence assistant.

Your role:
- Analyze business questions and provide clear, actionable insights
- When given data context, generate relevant analysis
- Present numbers clearly with comparisons and trends
- Keep responses concise and well-structured
- Use bullet points and sections for clarity
- If a question is vague, provide a helpful general analysis
- If you cannot answer something, explain what data would be needed

Response format:
- Use markdown formatting for readability
- Bold key numbers and metrics
- Use bullet points for lists
- Keep responses under 300 words unless detailed analysis is requested"""

    @classmethod
    def _initialize(cls):
        if not cls._client:
            api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
            if not api_key:
                raise ValueError("GEMINI_API_KEY is missing. Cannot initialize GeminiClient.")
            cls._client = genai.Client(api_key=api_key)

    @classmethod
    def generate_embeddings(cls, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generates 768-dimensional embeddings using text-embedding-004.
        Implements chunk batching to avoid API payload limits.
        """
        cls._initialize()
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            result = cls._client.models.embed_content(
                model='text-embedding-004',
                contents=batch,
            )
            
            # Extract embeddings from the new SDK result format
            for embedding_obj in result.embeddings:
                all_embeddings.append(embedding_obj.values)
                
        return all_embeddings

    @classmethod
    def embed_query(cls, text: str) -> List[float]:
        """
        Generates an embedding for a search query.
        """
        cls._initialize()
        
        result = cls._client.models.embed_content(
            model='text-embedding-004',
            contents=text,
        )
        return result.embeddings[0].values

    @classmethod
    async def generate_analyst_response(cls, query: str) -> dict:
        """
        Send a query to Gemini and return the response.
        Returns { "response": str, "error": str | None }
        """
        cls._initialize()

        try:
            result = cls._client.models.generate_content(
                model='gemini-2.5-pro',
                contents=f"{cls.SYSTEM_PROMPT}\n\nUser Query: {query}",
            )
            return {
                "response": result.text,
                "error": None,
            }
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return {
                    "response": None,
                    "error": "Gemini API rate limit exceeded. Please wait a moment and try again.",
                }
            elif "403" in error_msg or "API_KEY" in error_msg.upper():
                return {
                    "response": None,
                    "error": "Invalid Gemini API key. Please check your API key config.",
                }
            else:
                return {
                    "response": None,
                    "error": f"AI Error: {error_msg}",
                }

    @classmethod
    async def analyze_dataset(cls, data_preview: str, question: str) -> dict:
        """
        Send a dataset preview and a question to Gemini and return the structured analysis.
        Returns { "response": str, "chart_config": dict, "error": str | None }
        """
        cls._initialize()
        from pydantic import BaseModel, Field
        from google.genai import types
        import json

        class ChartConfig(BaseModel):
            type: str = Field(description="The type of chart to render (e.g. 'bar', 'line', 'pie')")
            data: list[dict] = Field(description="Array of data objects with a 'name' (x-axis label) and 'value' (y-axis numeric value). E.g. [{'name': 'Jan', 'value': 100}]")

        class DatasetAnalysis(BaseModel):
            answer: str = Field(description="The natural language analysis and insight, formatted in markdown")
            chart_config: ChartConfig = Field(description="The configuration for rendering a Recharts chart based on the data")

        try:
            prompt = (
                f"You are an AI Business Analyst. Based on the following dataset preview:\n\n{data_preview}\n\n"
                f"User Question: {question}\n\n"
                "Please analyze the data and answer the question. Also provide a chart configuration to visualize the relevant metrics if applicable. If no chart makes sense, provide an empty data array."
            )
            result = cls._client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DatasetAnalysis,
                    temperature=0.2,
                )
            )
            parsed = json.loads(result.text)
            return {
                "response": parsed.get("answer", "No answer generated."),
                "chart_config": parsed.get("chart_config", {"type": "bar", "data": []}),
                "error": None
            }
        except Exception as e:
            return {
                "response": None,
                "chart_config": None,
                "error": f"AI Error: {str(e)}"
            }
