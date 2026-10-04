"""The data layer: named collections of JSON records in SQLite (a file, or memory in tests).
Routes use only this, so moving to Postgres later changes this file alone."""

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

Record = dict[str, Any]


class Store:
    def __init__(self, path: str | None = None) -> None:
        self._db = sqlite3.connect(
            path or os.environ.get("DATABASE_PATH", ":memory:"), check_same_thread=False
        )
        self._db.execute(
            "create table if not exists documents (id text primary key, collection text not null,"
            " data text not null, created_at text not null)"
        )

    def insert(self, collection: str, data: Record) -> Record:
        record = {**data, "id": uuid.uuid4().hex, "created_at": datetime.now(UTC).isoformat()}
        self._db.execute(
            "insert into documents values (?, ?, ?, ?)",
            (record["id"], collection, json.dumps(data), record["created_at"]),
        )
        self._db.commit()
        return record

    def get(self, collection: str, record_id: str) -> Record | None:
        row = self._db.execute(
            "select id, data, created_at from documents where collection = ? and id = ?",
            (collection, record_id),
        ).fetchone()
        return _record(row) if row else None

    def find(self, collection: str, limit: int = 100, **where: Any) -> list[Record]:
        rows = self._db.execute(
            "select id, data, created_at from documents where collection = ?"
            " order by created_at desc",
            (collection,),
        ).fetchall()
        records = [_record(r) for r in rows]
        return [r for r in records if all(r.get(k) == v for k, v in where.items())][:limit]

    def update(self, collection: str, record_id: str, changes: Record) -> Record | None:
        current = self.get(collection, record_id)
        if current is None:
            return None
        data = {k: v for k, v in {**current, **changes}.items() if k not in ("id", "created_at")}
        self._db.execute(
            "update documents set data = ? where collection = ? and id = ?",
            (json.dumps(data), collection, record_id),
        )
        self._db.commit()
        return self.get(collection, record_id)

    def remove(self, collection: str, record_id: str) -> bool:
        cursor = self._db.execute(
            "delete from documents where collection = ? and id = ?", (collection, record_id)
        )
        self._db.commit()
        return cursor.rowcount > 0


def _record(row: tuple[str, str, str]) -> Record:
    return {**json.loads(row[1]), "id": row[0], "created_at": row[2]}
