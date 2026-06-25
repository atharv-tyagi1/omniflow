"""DAG Validator for OmniFlow workflows."""

from typing import Any, Dict, List, Set
from collections import defaultdict, deque

class WorkflowValidationError(Exception):
    pass

class WorkflowValidator:
    def __init__(self, max_nodes: int = 50, max_edges: int = 100, max_depth: int = 15, max_parallel: int = 5):
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.max_depth = max_depth
        self.max_parallel = max_parallel

    def validate(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        if len(nodes) > self.max_nodes:
            raise WorkflowValidationError(f"Workflow exceeds maximum of {self.max_nodes} nodes.")
        if len(edges) > self.max_edges:
            raise WorkflowValidationError(f"Workflow exceeds maximum of {self.max_edges} edges.")

        node_ids = {n["id"] for n in nodes}
        triggers = [n for n in nodes if n.get("type", "").startswith("trigger.")]

        if not triggers:
            raise WorkflowValidationError("Workflow must have at least one trigger node.")
        if len(triggers) > 1:
            raise WorkflowValidationError("Workflow cannot have multiple trigger nodes.")

        # Build adjacency list
        adj = defaultdict(list)
        in_degree = {nid: 0 for nid in node_ids}
        
        for edge in edges:
            u, v = edge.get("source"), edge.get("target")
            if not u or not v:
                continue
            if u not in node_ids or v not in node_ids:
                raise WorkflowValidationError(f"Edge references invalid node: {u} -> {v}")
            adj[u].append(v)
            in_degree[v] += 1

        # Cycle detection and topological sort
        visited = set()
        queue = deque()
        
        for nid in node_ids:
            if in_degree[nid] == 0:
                queue.append(nid)

        top_order = []
        while queue:
            # Check parallel width
            if len(queue) > self.max_parallel:
                raise WorkflowValidationError(f"Workflow exceeds maximum parallel branches of {self.max_parallel}.")
                
            curr = queue.popleft()
            top_order.append(curr)
            visited.add(curr)
            
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(top_order) != len(nodes):
            raise WorkflowValidationError("Workflow contains cycles.")

        # Check disconnected nodes
        trigger_id = triggers[0]["id"]
        reachable = set()
        def dfs(node):
            reachable.add(node)
            for neighbor in adj[node]:
                if neighbor not in reachable:
                    dfs(neighbor)
        
        dfs(trigger_id)
        if len(reachable) != len(nodes):
            raise WorkflowValidationError("Workflow contains disconnected nodes not reachable from trigger.")

        # Check max depth
        depths = {nid: 0 for nid in node_ids}
        depths[trigger_id] = 1
        max_seen_depth = 1
        for u in top_order:
            for v in adj[u]:
                depths[v] = max(depths[v], depths[u] + 1)
                max_seen_depth = max(max_seen_depth, depths[v])

        if max_seen_depth > self.max_depth:
            raise WorkflowValidationError(f"Workflow exceeds maximum depth of {self.max_depth}.")
