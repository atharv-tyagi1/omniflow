"""Core Agent Runtime Engine — the generic orchestrator for ALL OmniFlow agents.

Architecture (strictly followed):
  Request → Context Assembly → Prompt Construction → Knowledge Retrieval
  → Memory Retrieval → Tool Resolution → Model Selection → LLM Execution
  → Tool Calls → Workflow Calls → Response Generation → Persistence → Analytics
"""

import logging
import time
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.agent.runtime_context import RuntimeContext, ToolPolicy, ModelConfig
from backend.app.core.agent.context_builder import ContextBuilder
from backend.app.core.agent.prompt_engine import PromptEngine
from backend.app.core.agent.memory_engine import MemoryEngine
from backend.app.core.agent.knowledge_engine import KnowledgeEngine
from backend.app.core.agent.conversation_engine import ConversationEngine
from backend.app.core.agent.telemetry import TelemetryEngine
from backend.app.core.agent.tool_engine import ToolEngine
from backend.app.core.agent.reasoning_layer import ReasoningLayer
from backend.app.core.agent.exceptions import (
    MaxRecursionError,
    AgentRuntimeError,
    ProviderTimeoutError,
    ToolPolicyDenialError,
)
from backend.app.core.ai.providers.registry import provider_registry

logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    The single, generic Agent Engine that powers every AI agent in OmniFlow.
    Handles Customer Agents, Workspace Agents, and future Custom Agents.
    No agent-specific logic lives here — everything is configuration-driven.

    Execution pipeline (deterministic, non-reorderable):
        Request → Context → Prompt → Knowledge → Memory → Tools → Model → LLM
        → Tool Loop → Response → Persistence → Analytics
    """

    MAX_TOOL_CALLS_PER_TURN = 5
    MAX_WORKFLOW_HOPS_PER_TURN = 3

    def __init__(self):
        self.context_builder = ContextBuilder()
        self.prompt_engine = PromptEngine()
        self.memory_engine = MemoryEngine()
        self.knowledge_engine = KnowledgeEngine()
        self.conversation_engine = ConversationEngine()
        self.telemetry = TelemetryEngine()
        self.tool_engine = ToolEngine()
        self.tool_engine.register_defaults()

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ──────────────────────────────────────────────────────────────────────────

    async def execute(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        version_id: UUID,
        conversation_id: UUID,
        user_message: str,
        agent_config: Dict[str, Any],
        workspace_policies: str = "",
        is_public_allowed: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes a single agent turn end-to-end.
        Creates a run record, assembles context, calls the LLM (with tool loop),
        persists all trace data, and returns the response.
        """
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        # Build typed context object
        ctx = RuntimeContext(
            request_id=request_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            version_id=version_id,
            conversation_id=conversation_id,
            agent_name=agent_config.get("agent_name", "Agent"),
            agent_category=agent_config.get("category", "general"),
            is_public_allowed=is_public_allowed,
            workspace_policies=workspace_policies,
            system_prompt=agent_config.get("system_prompt", "You are a helpful AI assistant."),
            agent_prompt=agent_config.get("agent_prompt", ""),
            model_config=ModelConfig(
                provider=agent_config.get("provider", "gemini"),
                model_name=agent_config.get("model", ""),
                temperature=agent_config.get("temperature", 0.7),
                max_tokens=agent_config.get("max_tokens"),
            ),
            tool_policies=[
                ToolPolicy(**p) if isinstance(p, dict) else p
                for p in agent_config.get("tool_policies", [])
            ],
            prompt_version_id=UUID(agent_config["prompt_version_id"])
            if agent_config.get("prompt_version_id")
            else None,
        )

        # 1. Create AgentRun record
        run = await self.telemetry.create_run(
            db=db,
            workspace_id=workspace_id,
            agent_id=agent_id,
            version_id=version_id,
            conversation_id=conversation_id,
        )
        ctx.run_id = run.id

        # 2. Ensure conversation exists + participant logic
        conv = await self.conversation_engine.get_or_create_conversation(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
        )
        
        # Resolve active participant and load handoff state
        active_participant_id = await self.conversation_engine.resolve_active_participant(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
        )
        
        if conv.handoff_status == "pending":
            logger.info(f"[{request_id}] Conversation {conversation_id} is in pending handoff. Agent aborting turn.")
            return {
                "request_id": request_id,
                "content": "A human agent will be with you shortly.",
                "status": "handoff_pending",
                "run_id": str(run.id),
                "latency_ms": int((time.monotonic() - start_time) * 1000),
                "tokens_used": 0,
                "tool_calls": [],
                "knowledge_used": False,
                "memory_used": False,
            }
            
        await self.conversation_engine.register_agent_participant(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            run_id=run.id,
        )

        # Structured log: request start
        await self.telemetry.log(
            db=db,
            workspace_id=workspace_id,
            agent_id=agent_id,
            run_id=run.id,
            level="info",
            message="Agent run started",
            details=ctx.to_log_dict(),
        )

        run_status = "failed"
        final_response = ""
        total_tokens = 0

        try:
            # ──────────────────────────────────────────────────────────────────
            # 3. MEMORY RETRIEVAL (with graceful fallback)
            # ──────────────────────────────────────────────────────────────────
            try:
                memory_context, memory_refs = await self.memory_engine.compile_memory_context(
                    db=db,
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                )
            except Exception as e:
                logger.error(f"[{request_id}] Memory retrieval failed: {e}", exc_info=True)
                memory_context, memory_refs = "", []
                
            ctx.workspace_memory = memory_context
            ctx.memory_references = memory_refs

            # ──────────────────────────────────────────────────────────────────
            # 4. KNOWLEDGE RETRIEVAL (with graceful fallback)
            # ──────────────────────────────────────────────────────────────────
            try:
                knowledge_context, knowledge_refs = await self.knowledge_engine.retrieve_knowledge(
                    db=db,
                    query=user_message,
                    workspace_id=workspace_id,
                )
            except Exception as e:
                logger.error(f"[{request_id}] Knowledge retrieval failed: {e}", exc_info=True)
                knowledge_context, knowledge_refs = "", []
                
            ctx.knowledge_context = knowledge_context
            ctx.knowledge_references = knowledge_refs

            # ──────────────────────────────────────────────────────────────────
            # 5. TOOL RESOLUTION
            # ──────────────────────────────────────────────────────────────────
            policy_dicts = [
                {
                    "tool_type": p.tool_type,
                    "tool_config": p.tool_config,
                    "allowed_inputs": p.allowed_inputs,
                    "allowed_outputs": p.allowed_outputs,
                    "rate_limit": p.rate_limit,
                    "approval_required": p.approval_required,
                }
                for p in ctx.tool_policies
            ]
            available_tools = self.tool_engine.get_available_tools(policy_dicts)
            ctx.available_tool_names = [t["name"] for t in available_tools]

            tool_context = ""
            if ctx.available_tool_names:
                tool_context = "Available tools: " + ", ".join(ctx.available_tool_names)

            # ──────────────────────────────────────────────────────────────────
            # 6. CONTEXT BUILDER → LLM MESSAGE LIST (Enforcing 12-step assembly)
            # ──────────────────────────────────────────────────────────────────
            model_conf_str = f"Model: {ctx.model_config.model_name}, Temp: {ctx.model_config.temperature}"
            
            messages = await self.context_builder.build_messages(
                workspace_policies=ctx.workspace_policies,
                system_prompt=ctx.system_prompt,
                agent_prompt=ctx.agent_prompt,
                conversation_context=f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')} Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}",
                workspace_memory=memory_context,
                agent_memory="",
                conversation_memory="",
                knowledge_retrieval=knowledge_context,
                tool_availability=tool_context,
                workflow_availability="",
                model_configuration=model_conf_str,
                conversation_history=[],  # Normally passed from conversation_engine
                user_message=user_message,
            )

            # ──────────────────────────────────────────────────────────────────
            # 8. MODEL SELECTION
            # ──────────────────────────────────────────────────────────────────
            task_type = ReasoningLayer.estimate_task_type(user_message)
            model = ReasoningLayer.select_model(
                agent_config={
                    "provider": ctx.model_config.provider,
                    "model": ctx.model_config.model_name,
                },
                task_type=task_type,
            )

            provider = provider_registry.get_provider(ctx.model_config.provider)

            # ──────────────────────────────────────────────────────────────────
            # 9. LLM EXECUTION LOOP (with tool call support)
            # ──────────────────────────────────────────────────────────────────
            tool_call_count = 0
            workflow_hop_count = 0
            policy_denial_count = 0
            llm_start = time.monotonic()

            while True:
                llm_response = await provider.generate_completion(
                    messages=messages,
                    model=model,
                    temperature=ctx.model_config.temperature,
                    max_tokens=ctx.model_config.max_tokens,
                    tools=available_tools if available_tools else None,
                )

                if llm_response.get("error"):
                    raise AgentRuntimeError(f"Provider error: {llm_response['error']}")

                total_tokens += llm_response.get("usage", {}).get("total_tokens", 0)

                # Check for tool calls
                if llm_response.get("tool_calls"):
                    if tool_call_count >= self.MAX_TOOL_CALLS_PER_TURN:
                        raise MaxRecursionError("Maximum tool calls per turn exceeded.")

                    for tool_call in llm_response["tool_calls"]:
                        tool_name = tool_call.get("function", {}).get("name", "")
                        tool_args = tool_call.get("function", {}).get("arguments", {})
                        if isinstance(tool_args, str):
                            import json
                            try:
                                tool_args = json.loads(tool_args)
                            except Exception:
                                tool_args = {}

                        # Inject workspace context for tools that need it
                        tool_args["workspace_id"] = str(workspace_id)
                        tool_args["db"] = db

                        try:
                            tool_result = await self.tool_engine.execute_tool(
                                tool_name=tool_name,
                                kwargs=tool_args,
                                tool_policies=policy_dicts,
                                workspace_id=str(workspace_id),
                            )
                            if tool_name == "workflow":
                                workflow_hop_count += 1
                                if workflow_hop_count > self.MAX_WORKFLOW_HOPS_PER_TURN:
                                    raise MaxRecursionError("Maximum workflow hops per turn exceeded.")
                        except ToolPolicyDenialError as e:
                            logger.warning(f"[{request_id}] Tool policy denial: {e}")
                            tool_result = {"status": "error", "error": str(e)}
                            policy_denial_count += 1
                            if policy_denial_count >= 3:
                                raise AgentRuntimeError("Execution aborted due to repeated policy denials.")
                        except Exception as e:
                            logger.error(f"[{request_id}] Tool execution failed: {e}", exc_info=True)
                            tool_result = {"status": "error", "error": f"Tool execution failed: {str(e)}"}

                        ctx.tool_calls_trace.append({
                            "tool": tool_name,
                            "args": {k: v for k, v in tool_args.items() if k not in ("db",)},
                            "result_status": tool_result.get("status", "error"),
                        })

                        # Append tool result to messages and continue loop
                        messages.append({
                            "role": "tool",
                            "content": str(tool_result),
                            "tool_call_id": tool_call.get("id", ""),
                        })

                    tool_call_count += 1
                    continue  # Loop back for final LLM response

                # No tool calls → final response
                final_response = llm_response.get("content") or ""
                break

            llm_latency_ms = int((time.monotonic() - llm_start) * 1000)

            # ──────────────────────────────────────────────────────────────────
            # 10. PERSIST CONVERSATION MEMORY
            # ──────────────────────────────────────────────────────────────────
            await self.memory_engine.save_turn(
                db=db,
                workspace_id=workspace_id,
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=final_response,
                token_metadata={"total_tokens": total_tokens},
            )

            # ──────────────────────────────────────────────────────────────────
            # 11. RECORD RUN STEP + DECISION TRACE
            # ──────────────────────────────────────────────────────────────────
            run_step = await self.telemetry.record_step(
                db=db,
                workspace_id=workspace_id,
                run_id=run.id,
                step_type="llm_call",
                payload={
                    "model": model,
                    "provider": ctx.model_config.provider,
                    "tokens": total_tokens,
                    "tool_calls": len(ctx.tool_calls_trace),
                },
                latency_ms=llm_latency_ms,
            )

            await self.telemetry.persist_decision_trace(
                db=db,
                workspace_id=workspace_id,
                run_step=run_step,
                prompt_version_id=ctx.prompt_version_id,
                memory_references=ctx.memory_references,
                knowledge_references=ctx.knowledge_references,
                tool_calls=ctx.tool_calls_trace,
                workflow_calls=ctx.workflow_calls_trace,
                model_used=f"{ctx.model_config.provider}/{model}",
                latency_ms=llm_latency_ms,
                cost_tokens=total_tokens,
                execution_metadata={
                    "request_id": request_id,
                    "task_type": task_type,
                    "tool_call_count": tool_call_count,
                },
            )

            # ──────────────────────────────────────────────────────────────────
            # 12. ANALYTICS HOOKS
            # ──────────────────────────────────────────────────────────────────
            estimated_cost = total_tokens * 0.000001  # Placeholder cost rate
            await self.telemetry.increment_metric(
                db=db,
                workspace_id=workspace_id,
                agent_id=agent_id,
                tokens=total_tokens,
                cost=estimated_cost,
            )

            # Update conversation active responder
            await self.conversation_engine.update_active_responder(
                db=db,
                conversation_id=conversation_id,
                workspace_id=workspace_id,
                run_id=run.id,
            )

            run_status = "success"

        except MaxRecursionError as e:
            logger.error(f"[{request_id}] Max recursion exceeded: {e}")
            final_response = (
                "I'm sorry, I encountered a complexity limit. "
                "Please try rephrasing your request."
            )
            run_status = "failed"

        except ProviderTimeoutError as e:
            logger.error(f"[{request_id}] Provider timeout: {e}")
            final_response = (
                "The AI service is temporarily unavailable. Please try again in a moment."
            )
            run_status = "failed"

        except asyncio.CancelledError as e:
            logger.warning(f"[{request_id}] AgentRuntime execution cancelled (e.g. client disconnected).")
            run_status = "cancelled"
            
            # Durably record the cancellation in a separate DB session so it survives any transaction rollback!
            from backend.app.core.database import AsyncSessionLocal
            from backend.app.models.agent_log import AgentLog
            async with AsyncSessionLocal() as audit_db:
                audit_log = AgentLog(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    run_id=run.id if run else None,
                    level="warning",
                    message="Agent execution cancelled (client disconnected).",
                    details={"request_id": request_id, "reason": "client_disconnect"}
                )
                audit_db.add(audit_log)
                await audit_db.commit()
                
            raise e

        except Exception as e:
            logger.error(f"[{request_id}] AgentRuntime execution error: {e}", exc_info=True)
            final_response = (
                "I'm experiencing a technical issue. "
                "If this persists, please contact support."
            )
            run_status = "failed"

            # Log the error
            await self.telemetry.log(
                db=db,
                workspace_id=workspace_id,
                agent_id=agent_id,
                run_id=run.id if run else None,
                level="error",
                message=f"Runtime exception: {type(e).__name__}: {str(e)[:500]}",
                details={"request_id": request_id},
            )

        finally:
            # Always complete the run record
            total_latency_ms = int((time.monotonic() - start_time) * 1000)
            if run:
                await self.telemetry.complete_run(db=db, run=run, status=run_status)

            # Commit all telemetry atomically
            try:
                await db.commit()
            except Exception as commit_err:
                logger.error(f"[{request_id}] DB commit failed: {commit_err}")
                await db.rollback()

            logger.info(
                f"[{request_id}] AgentRuntime completed: "
                f"agent={agent_id} status={run_status} "
                f"latency={total_latency_ms}ms tokens={total_tokens}"
            )

        return {
            "request_id": request_id,
            "content": final_response,
            "status": run_status,
            "run_id": str(run.id) if run else None,
            "latency_ms": int((time.monotonic() - start_time) * 1000),
            "tokens_used": total_tokens,
            "tool_calls": ctx.tool_calls_trace,
            "knowledge_used": bool(ctx.knowledge_context),
            "memory_used": bool(ctx.workspace_memory or ctx.agent_memory),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # LEGACY COMPATIBILITY (for existing agent_service.py callers)
    # ──────────────────────────────────────────────────────────────────────────

    async def execute_turn(
        self,
        conversation_id: str,
        agent_config: Dict[str, Any],
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        workspace_policies: str = "",
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Legacy compatibility shim for existing callers that don't pass a DB session.
        New code should use execute() directly.
        """
        if db is not None:
            # New path: use db session passed in
            workspace_id = UUID(agent_config.get("workspace_id", str(uuid.uuid4())))
            agent_id = UUID(agent_config.get("agent_id", str(uuid.uuid4())))
            version_id = UUID(agent_config.get("version_id", str(uuid.uuid4())))
            conv_id = UUID(conversation_id)

            result = await self.execute(
                db=db,
                workspace_id=workspace_id,
                agent_id=agent_id,
                version_id=version_id,
                conversation_id=conv_id,
                user_message=user_message,
                agent_config=agent_config,
                workspace_policies=workspace_policies,
            )
            return result

        # Legacy path: use provider directly without DB persistence
        logger.warning(
            "execute_turn called without DB session — running in stateless mode. "
            "Telemetry and memory will not be persisted."
        )
        provider_name = agent_config.get("provider", "gemini")
        model = ReasoningLayer.select_model(agent_config)
        provider = provider_registry.get_provider(provider_name)

        messages = await self.context_builder.build_messages(
            workspace_policies=workspace_policies,
            system_prompt=agent_config.get("system_prompt", ""),
            agent_prompt=agent_config.get("agent_prompt", ""),
            conversation_context="",
            workspace_memory="",
            agent_memory="",
            conversation_memory="",
            knowledge_retrieval="",
            tool_availability="",
            workflow_availability="",
            model_configuration="",
            conversation_history=conversation_history,
            user_message=user_message,
        )

        try:
            response = await provider.generate_completion(
                messages=messages,
                model=model,
                temperature=agent_config.get("temperature", 0.7),
            )
            return {"content": response.get("content", ""), "status": "success"}
        except Exception as e:
            logger.error(f"Stateless execute_turn failed: {e}")
            return {"content": "I encountered an error. Please try again.", "status": "failed"}
