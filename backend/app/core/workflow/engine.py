"""Workflow Engine for DAG execution."""

import asyncio
from typing import Any, Dict, List
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.workflow_run import WorkflowRun
from backend.app.models.workflow_run_step import WorkflowRunStep
from backend.app.models.workflow_version import WorkflowVersion
from backend.app.models.workflow_node import WorkflowNode
from backend.app.models.workflow_edge import WorkflowEdge

from backend.app.core.workflow.executor import NodeExecutorFactory
from backend.app.core.workflow.validator import WorkflowValidator
from backend.app.core.workflow.nodes.base import NodeExecutionResult


class ExecutionContext:
    def __init__(self, run_id: str, trigger_data: Dict[str, Any]):
        self.run_id = run_id
        self.state: Dict[str, Any] = {"trigger_data": trigger_data}
        self.errors: List[Dict[str, Any]] = []


class WorkflowEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.validator = WorkflowValidator()
        self.node_timeout = 30.0
        self.workflow_timeout = 300.0
        self.max_retries = 3

    async def _fetch_dag(self, version_id: str):
        # Fetch nodes
        nodes_stmt = select(WorkflowNode).where(WorkflowNode.version_id == version_id)
        nodes_result = await self.session.execute(nodes_stmt)
        nodes = nodes_result.scalars().all()
        
        # Fetch edges
        edges_stmt = select(WorkflowEdge).where(WorkflowEdge.version_id == version_id)
        edges_result = await self.session.execute(edges_stmt)
        edges = edges_result.scalars().all()
        
        return nodes, edges

    async def _log_event(self, workspace_id: str, event_type: str, message: str, workflow_id: str = None, run_id: str = None, step_id: str = None):
        from backend.app.models.workflow_log import WorkflowLog
        log = WorkflowLog(
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            run_id=run_id,
            step_id=step_id,
            event_type=event_type,
            message=message
        )
        self.session.add(log)
        await self.session.commit()

    async def _execute_node_with_retry(self, executor, context_state: Dict[str, Any]) -> NodeExecutionResult:
        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.wait_for(executor.execute(context_state), timeout=self.node_timeout)
                if result.status == "success":
                    return result
            except asyncio.TimeoutError:
                result = NodeExecutionResult.failed({"error": "Node execution timed out"})
            except Exception as e:
                result = NodeExecutionResult.failed({"error": str(e)})
            
            if attempt < self.max_retries:
                await asyncio.sleep(2 ** attempt) # Exponential backoff: 1s, 2s, 4s
                
        return result

    async def execute_run(self, run_id: str, trigger_data: Dict[str, Any]):
        stmt = select(WorkflowRun).where(WorkflowRun.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError("Run not found")
            
        run.status = "running"
        await self.session.commit()
        
        await self._log_event(run.workflow.workspace_id, "run_started", "Workflow execution started", run.workflow_id, run.id)

        context = ExecutionContext(run_id, trigger_data)
        
        try:
            nodes, edges = await self._fetch_dag(run.version_id)
            
            # Build structures
            nodes_map = {str(n.id): {"type": n.type, "config": n.config} for n in nodes}
            adj = {str(n.id): [] for n in nodes}
            for e in edges:
                adj[str(e.source_node_id)].append({
                    "target": str(e.target_node_id),
                    "source_handle": e.source_handle,
                    "target_handle": e.target_handle
                })

            # Find trigger node
            trigger_id = None
            for nid, n in nodes_map.items():
                if n["type"].startswith("trigger."):
                    trigger_id = nid
                    break
                    
            if not trigger_id:
                raise ValueError("No trigger node found")

            # BFS Execution
            queue = [trigger_id]
            
            async def execute_with_timeout():
                while queue:
                    curr_id = queue.pop(0)
                    node_data = nodes_map[curr_id]
                    
                    executor = NodeExecutorFactory.get_executor(curr_id, node_data["type"], node_data["config"])
                    
                    # Record step start
                    step = WorkflowRunStep(
                        run_id=run_id,
                        node_id=curr_id,
                        status="running",
                        input_payload=context.state.copy()
                    )
                    self.session.add(step)
                    await self.session.commit()
                    
                    result = await self._execute_node_with_retry(executor, context.state)
                    
                    step.status = result.status
                    step.output_payload = result.output
                    step.error_payload = result.error
                    step.completed_at = datetime.now(timezone.utc)
                    await self.session.commit()
                    
                    await self._log_event(
                        run.workflow.workspace_id, 
                        "node_executed", 
                        f"Node {node_data['type']} completed with {result.status}", 
                        run.workflow_id, 
                        run.id, 
                        step.id
                    )
                    
                    if result.status == "success":
                        context.state[curr_id] = result.output
                        
                        # Branching logic
                        for edge in adj[curr_id]:
                            if node_data["type"] == "condition.if_else":
                                matched = result.output.get("matched", False)
                                if (matched and edge["source_handle"] == "true") or \
                                   (not matched and edge["source_handle"] == "false"):
                                    queue.append(edge["target"])
                            else:
                                queue.append(edge["target"])
            
            # Workflow timeout
            await asyncio.wait_for(execute_with_timeout(), timeout=self.workflow_timeout)
            
            run.status = "success"
            run.execution_log = {"message": "Executed successfully"}
            await self._log_event(run.workflow.workspace_id, "run_success", "Workflow execution succeeded", run.workflow_id, run.id)
            
        except asyncio.TimeoutError:
            run.status = "failed"
            run.execution_log = {"error": "Workflow execution timed out"}
            await self._log_event(run.workflow.workspace_id, "run_failed", "Workflow execution timed out", run.workflow_id, run.id)
        except Exception as e:
            run.status = "failed"
            run.execution_log = {"error": str(e)}
            await self._log_event(run.workflow.workspace_id, "run_failed", f"Workflow failed: {str(e)}", run.workflow_id, run.id)
        finally:
            await self.session.commit()
