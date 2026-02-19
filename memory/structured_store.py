"""Async interface for structured persistent memory."""

import json
from typing import Any

from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL
from memory.db_models import AuditLog, Base, Conversation, Summary, Task


def _get_engine():
    """Create async engine from DATABASE_URL."""
    return create_async_engine(
        DATABASE_URL,
        echo=False,
    )


def _get_session_factory(engine):
    """Create async session factory."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


class StructuredMemoryStore:
    """Async store for conversations, tasks, and summaries."""

    def __init__(self, database_url: str | None = None) -> None:
        url = database_url or DATABASE_URL
        self._engine = create_async_engine(url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def init_db(self) -> None:
        """Create all tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def append_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append a conversation entry."""
        async with self._session_factory() as session:
            conv = Conversation(session_id=session_id, role=role, content=content)
            session.add(conv)
            await session.commit()

    async def get_conversations(
        self,
        session_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent conversations for a session."""
        async with self._session_factory() as session:
            stmt = (
                select(Conversation)
                .where(Conversation.session_id == session_id)
                .order_by(Conversation.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [
            {"role": r.role, "content": r.content, "timestamp": r.timestamp.isoformat()}
            for r in reversed(rows)
        ]

    async def get_conversations_all_sessions(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get recent conversation turns across all sessions, ordered by timestamp (most recent first)."""
        async with self._session_factory() as session:
            stmt = (
                select(Conversation)
                .order_by(Conversation.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [
            {
                "role": r.role,
                "content": r.content,
                "timestamp": r.timestamp.isoformat(),
                "session_id": r.session_id,
            }
            for r in reversed(rows)
        ]

    async def upsert_task(
        self,
        session_id: str,
        task_id: str,
        title: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Insert or update a task."""
        meta_json = json.dumps(metadata or {})
        async with self._session_factory() as session:
            stmt = select(Task).where(Task.id == task_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.title = title
                existing.status = status
                existing.metadata_json = meta_json
                existing.updated_at = datetime.utcnow()
            else:
                task = Task(
                    id=task_id,
                    session_id=session_id,
                    title=title,
                    status=status,
                    metadata_json=meta_json,
                )
                session.add(task)
            await session.commit()

    async def get_tasks(self, session_id: str) -> list[dict[str, Any]]:
        """Get all tasks for a session."""
        async with self._session_factory() as session:
            stmt = select(Task).where(Task.session_id == session_id).order_by(Task.created_at)
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "metadata": json.loads(r.metadata_json),
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]

    async def get_task(self, session_id: str, task_id: str) -> dict[str, Any] | None:
        """Get a single task by ID."""
        async with self._session_factory() as session:
            stmt = select(Task).where(
                Task.id == task_id,
                Task.session_id == session_id,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "title": row.title,
            "status": row.status,
            "metadata": json.loads(row.metadata_json),
            "created_at": row.created_at.isoformat(),
        }

    async def append_summary(self, session_id: str, content: str) -> None:
        """Append a summary for a session."""
        async with self._session_factory() as session:
            summary = Summary(session_id=session_id, content=content)
            session.add(summary)
            await session.commit()

    async def get_summaries(self, session_id: str, limit: int = 10) -> list[str]:
        """Get recent summaries for a session."""
        async with self._session_factory() as session:
            stmt = (
                select(Summary)
                .where(Summary.session_id == session_id)
                .order_by(Summary.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [r.content for r in rows]

    async def append_audit_log(
        self,
        run_id: str,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Append an audit log entry."""
        import json

        async with self._session_factory() as session:
            log = AuditLog(
                run_id=run_id,
                session_id=session_id,
                event_type=event_type,
                payload=json.dumps(payload),
            )
            session.add(log)
            await session.commit()

    async def forget_old_entries(
        self,
        session_id: str,
        before_date: date,
    ) -> int:
        """Prune conversations and summaries older than before_date. Returns count deleted."""
        async with self._session_factory() as session:
            before_dt = datetime.combine(before_date, datetime.min.time())
            conv_del = delete(Conversation).where(
                Conversation.session_id == session_id,
                Conversation.timestamp < before_dt,
            )
            sum_del = delete(Summary).where(
                Summary.session_id == session_id,
                Summary.created_at < before_dt,
            )
            r1 = await session.execute(conv_del)
            r2 = await session.execute(sum_del)
            await session.commit()
            return (r1.rowcount or 0) + (r2.rowcount or 0)

    async def close(self) -> None:
        """Close the engine."""
        await self._engine.dispose()
