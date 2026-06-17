from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.db_models.nexus_one import MemoryGraphEdge, MemoryGraphNode


class MemoryGraph:
    """Enterprise memory graph — stores objectives, decisions, outcomes, lessons."""

    @staticmethod
    def store(
        db: Session,
        *,
        tenant_id: str,
        node_type: str,
        title: str,
        content: dict[str, Any],
        objective_id: str | None = None,
        link_to_id: str | None = None,
        relationship: str = "relates_to",
    ) -> MemoryGraphNode:
        node = MemoryGraphNode(
            tenant_id=tenant_id,
            objective_id=objective_id,
            node_type=node_type,
            title=title,
            content=content,
        )
        db.add(node)
        db.flush()

        if link_to_id:
            edge = MemoryGraphEdge(
                tenant_id=tenant_id,
                source_id=link_to_id,
                target_id=node.id,
                relationship=relationship,
            )
            db.add(edge)

        db.commit()
        db.refresh(node)
        return node

    @staticmethod
    def retrieve_for_objective(db: Session, tenant_id: str, objective_id: str) -> list[MemoryGraphNode]:
        return (
            db.query(MemoryGraphNode)
            .filter(MemoryGraphNode.tenant_id == tenant_id, MemoryGraphNode.objective_id == objective_id)
            .order_by(MemoryGraphNode.created_at.asc())
            .all()
        )

    @staticmethod
    def search(db: Session, tenant_id: str, node_type: str | None = None, limit: int = 50) -> list[MemoryGraphNode]:
        q = db.query(MemoryGraphNode).filter(MemoryGraphNode.tenant_id == tenant_id)
        if node_type:
            q = q.filter(MemoryGraphNode.node_type == node_type)
        return q.order_by(MemoryGraphNode.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_context_for_agents(db: Session, tenant_id: str, objective_id: str) -> dict[str, Any]:
        nodes = MemoryGraph.retrieve_for_objective(db, tenant_id, objective_id)
        return {
            "objective_memories": [{"type": n.node_type, "title": n.title, "content": n.content} for n in nodes],
            "lessons_learned": [n.content for n in nodes if n.node_type == "lesson_learned"],
            "decisions": [n.content for n in nodes if n.node_type == "decision"],
            "outcomes": [n.content for n in nodes if n.node_type == "outcome"],
        }
