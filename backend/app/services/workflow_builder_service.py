import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.workflow import Workflow
from backend.app.models.workflow_version import WorkflowVersion
from backend.app.models.workflow_node import WorkflowNode
from backend.app.models.workflow_edge import WorkflowEdge
from backend.app.schemas.workflow_builder import WorkflowDraftUpdate
from backend.app.core.exceptions import NotFoundError

class WorkflowBuilderService:
    @staticmethod
    async def get_workflow_draft(db: AsyncSession, workspace_id: uuid.UUID, workflow_id: uuid.UUID) -> dict:
        stmt = select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace_id)
        res = await db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise NotFoundError("Workflow not found")

        # Get draft version (is_published=False)
        stmt_ver = select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id, 
            WorkflowVersion.is_published == False
        ).order_by(WorkflowVersion.version_number.desc())
        res_ver = await db.execute(stmt_ver)
        draft_version = res_ver.scalars().first()

        nodes = []
        edges = []
        version_id = None

        if draft_version:
            version_id = draft_version.id
            stmt_nodes = select(WorkflowNode).where(WorkflowNode.version_id == version_id)
            res_nodes = await db.execute(stmt_nodes)
            nodes = res_nodes.scalars().all()

            stmt_edges = select(WorkflowEdge).where(WorkflowEdge.version_id == version_id)
            res_edges = await db.execute(stmt_edges)
            edges = res_edges.scalars().all()

        return {
            "workflow": {
                "id": str(workflow.id),
                "name": workflow.name,
                "trigger_type": workflow.trigger_type,
                "status": workflow.status,
                "active_version_id": str(workflow.active_version_id) if workflow.active_version_id else None
            },
            "draft_version_id": str(version_id) if version_id else None,
            "nodes": [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "position_x": n.ui_position.get("x", 0.0),
                    "position_y": n.ui_position.get("y", 0.0),
                    "config": n.config
                } for n in nodes
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "source": str(e.source_node_id),
                    "target": str(e.target_node_id),
                    "source_handle": e.source_handle,
                    "target_handle": e.target_handle
                } for e in edges
            ]
        }

    @staticmethod
    async def save_draft(db: AsyncSession, workspace_id: uuid.UUID, workflow_id: uuid.UUID, draft: WorkflowDraftUpdate):
        # Verify workflow
        stmt = select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace_id)
        res = await db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise NotFoundError("Workflow not found")

        # Find or create draft version
        stmt_ver = select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id, 
            WorkflowVersion.is_published == False
        ).order_by(WorkflowVersion.version_number.desc())
        res_ver = await db.execute(stmt_ver)
        draft_version = res_ver.scalars().first()

        if not draft_version:
            # Check highest version number
            stmt_highest = select(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow_id).order_by(WorkflowVersion.version_number.desc())
            res_highest = await db.execute(stmt_highest)
            highest = res_highest.scalars().first()
            next_num = (highest.version_number + 1) if highest else 1

            draft_version = WorkflowVersion(
                workflow_id=workflow_id,
                version_number=next_num,
                is_published=False
            )
            db.add(draft_version)
            await db.flush()

        # Delete existing nodes and edges for this version
        stmt_del_edges = select(WorkflowEdge).where(WorkflowEdge.version_id == draft_version.id)
        res_del_edges = await db.execute(stmt_del_edges)
        for e in res_del_edges.scalars().all():
            await db.delete(e)

        stmt_del_nodes = select(WorkflowNode).where(WorkflowNode.version_id == draft_version.id)
        res_del_nodes = await db.execute(stmt_del_nodes)
        for n in res_del_nodes.scalars().all():
            await db.delete(n)

        await db.flush()

        # Insert new nodes and edges
        # We need to map string IDs from frontend to UUIDs, or let frontend generate UUIDs.
        # Assuming frontend generates valid UUIDs for nodes/edges
        node_id_map = {}
        for n in draft.nodes:
            nid = uuid.UUID(n.id) if len(n.id) == 36 else uuid.uuid4()
            node_id_map[n.id] = nid
            node = WorkflowNode(
                id=nid,
                version_id=draft_version.id,
                type=n.type,
                config=n.config,
                ui_position={"x": n.position_x, "y": n.position_y}
            )
            db.add(node)

        for e in draft.edges:
            eid = uuid.UUID(e.id) if len(e.id) == 36 else uuid.uuid4()
            source_id = node_id_map.get(e.source, uuid.UUID(e.source) if len(e.source) == 36 else None)
            target_id = node_id_map.get(e.target, uuid.UUID(e.target) if len(e.target) == 36 else None)
            if not source_id or not target_id:
                continue

            edge = WorkflowEdge(
                id=eid,
                version_id=draft_version.id,
                source_node_id=source_id,
                target_node_id=target_id,
                source_handle=e.source_handle,
                target_handle=e.target_handle
            )
            db.add(edge)

        # Update workflow's updated_at
        workflow.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return {"status": "success", "draft_version_id": str(draft_version.id)}

    @staticmethod
    async def publish(db: AsyncSession, workspace_id: uuid.UUID, workflow_id: uuid.UUID):
        # Verify workflow
        stmt = select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == workspace_id)
        res = await db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise NotFoundError("Workflow not found")

        # Find draft version
        stmt_ver = select(WorkflowVersion).where(
            WorkflowVersion.workflow_id == workflow_id, 
            WorkflowVersion.is_published == False
        ).order_by(WorkflowVersion.version_number.desc())
        res_ver = await db.execute(stmt_ver)
        draft_version = res_ver.scalars().first()

        if not draft_version:
            raise ValueError("No draft version found to publish")

        # Mark as published
        draft_version.is_published = True
        draft_version.published_at = datetime.now(timezone.utc)
        
        # Update workflow active_version_id
        workflow.active_version_id = draft_version.id
        workflow.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return {
            "status": "success", 
            "version_id": str(draft_version.id), 
            "version_number": draft_version.version_number
        }
