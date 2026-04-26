from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GridSize:
    rows: int
    cols: int


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def init_db(con: sqlite3.Connection, size: GridSize) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS grid (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          rows INTEGER NOT NULL,
          cols INTEGER NOT NULL
        );
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS cell (
          r INTEGER NOT NULL,
          c INTEGER NOT NULL,
          v TEXT NOT NULL DEFAULT '',
          PRIMARY KEY (r, c)
        );
        """
    )
    con.execute(
        "INSERT INTO grid (id, rows, cols) VALUES (1, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET rows=excluded.rows, cols=excluded.cols;",
        (size.rows, size.cols),
    )
    con.commit()


def get_grid_size(con: sqlite3.Connection) -> GridSize:
    row = con.execute("SELECT rows, cols FROM grid WHERE id = 1").fetchone()
    if not row:
        return GridSize(rows=50, cols=10)
    return GridSize(rows=int(row[0]), cols=int(row[1]))


def set_cell(con: sqlite3.Connection, r: int, c: int, v: str) -> None:
    con.execute(
        "INSERT INTO cell (r, c, v) VALUES (?, ?, ?) "
        "ON CONFLICT(r, c) DO UPDATE SET v=excluded.v;",
        (r, c, v),
    )
    con.commit()


def get_cells(con: sqlite3.Connection) -> dict[tuple[int, int], str]:
    out: dict[tuple[int, int], str] = {}
    for r, c, v in con.execute("SELECT r, c, v FROM cell"):
        out[(int(r), int(c))] = str(v) if v is not None else ""
    return out


def bulk_set_cells(con: sqlite3.Connection, items: Iterable[tuple[int, int, str]]) -> None:
    con.executemany(
        "INSERT INTO cell (r, c, v) VALUES (?, ?, ?) "
        "ON CONFLICT(r, c) DO UPDATE SET v=excluded.v;",
        list(items),
    )
    con.commit()


def insert_row(con: sqlite3.Connection, at_row: int) -> None:
    size = get_grid_size(con)
    at = max(0, min(at_row, size.rows))
    with con:
        # shift down from bottom to avoid PK collisions
        for (r,) in con.execute("SELECT r FROM cell WHERE r >= ? ORDER BY r DESC", (at,)).fetchall():
            con.execute("UPDATE cell SET r = r + 1 WHERE r = ?", (int(r),))
        con.execute("UPDATE grid SET rows = rows + 1 WHERE id = 1;")


def delete_row(con: sqlite3.Connection, row_idx: int) -> None:
    size = get_grid_size(con)
    if size.rows <= 0:
        return
    r0 = max(0, min(row_idx, size.rows - 1))
    with con:
        con.execute("DELETE FROM cell WHERE r = ?", (r0,))
        for (r,) in con.execute("SELECT r FROM cell WHERE r > ? ORDER BY r ASC", (r0,)).fetchall():
            con.execute("UPDATE cell SET r = r - 1 WHERE r = ?", (int(r),))
        con.execute("UPDATE grid SET rows = rows - 1 WHERE id = 1;")


def clear_cells(con: sqlite3.Connection) -> None:
    with con:
        con.execute("DELETE FROM cell;")


