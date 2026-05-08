from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, List
from datetime import datetime

@dataclass(frozen=True)
class DeclareForm:
    nvl_code: Optional[str] = None
    bill: Optional[str] = None
    invoice: Optional[str] = None
    declare_code: Optional[str] = None
    type_code: Optional[str] = None
    route_type: Optional[str] = None
    term: Optional[str] = None
    date: Optional[str] = None
    month: Optional[int] = None
    tms: Optional[str] = None
    form_code: Optional[str] = None
    method: Optional[str] = None
    time: Optional[str] = None

def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con

def init_db(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS folder (
          id INTEGER PRIMARY KEY,
          name varchar(100) NOT NULL,
          origin_path varchar(600) NOT NULL,
          date varchar(20) UNIQUE NOT NULL
        );
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS declare_form (
            id INTEGER PRIMARY KEY,
            folder_id INTEGER NOT NULL,
            nvl_code VARCHAR(20) NOT NULL,
            bill VARCHAR(20),
            invoice VARCHAR(20),
            declare_code VARCHAR(20),
            type_code VARCHAR(20),
            route_type VARCHAR(20),
            term VARCHAR(20),
            date VARCHAR(20),
            tms VARCHAR(20),
            form_code VARCHAR(20),
            method VARCHAR(20),
            progress VARCHAR(20),
            mail_time VARCHAR(20),
            tms_time VaRCHAR(20),
            draft_time VARCHAR(20),
            tk_time VARCHAR(20),
            official_time VARCHAR(20),
            passed_time VARCHAR(20),
            FOREIGN KEY (folder_id) REFERENCES folder(id),
            UNIQUE(folder_id, nvl_code)
        );
        """
    )

    con.commit()
    
def save_cell(con, column_name, record_id, value):
    con.execute(
        f"UPDATE declare_form SET {column_name} = ? WHERE id = ?",
        (value, record_id)
    )

    con.commit()

    print(f"Saved row {record_id}, column {column_name} = {value}")   

def get_active_folder(con: sqlite3.Connection) -> list[dict]:
    rows = con.execute(
        "SELECT name, origin_path, date, id FROM folder ORDER BY date desc"
    ).fetchall()

    return [dict(row) for row in rows]

def get_declare_forms(con, folder_id=None):
    print("Getting declare forms for folder_id:", folder_id)
    try:
        cur = con.cursor()
        con.row_factory = sqlite3.Row
        if folder_id:
            cur.execute(
                """SELECT 
                    id, folder_id,
                    nvl_code, 
                    bill, 
                    invoice, 
                    type_code,
                    progress, 

                    date,
                    declare_code,
                    route_type,
                    form_code,
                    term,  
                    tms,  
                    mail_time,
                    tms_time,
                    draft_time,
                    tk_time,
                    official_time,
                    passed_time,
                    method
                FROM declare_form WHERE folder_id = ?

                """,
                (folder_id,)
            )
        else:
            return None
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print("❌ EXECUTEMANY ERROR:", e)
        raise

def save_declare_forms(con, records: list[list], fields: list[str]):
    """
    Save declare forms using list-based records and dynamic fields.
    """

    # Build update fields (exclude folder_id + nvl_code)
    update_fields = [
        f"{field} = excluded.{field}"
        for field in fields
        if field not in ("id", "folder_id")
    ]

    field_sql = ",\n                ".join(fields)
    update_sql = ",\n                ".join(update_fields)

    # Build placeholders
    placeholders = ", ".join(["?"] * len(fields))
    sql = f"""
        INSERT INTO declare_form (
                {field_sql}
        ) VALUES ({placeholders})
        ON CONFLICT(id, folder_id)
        DO UPDATE SET
                {update_sql}
    """

    print("Executing SQL:")
    print(sql)
    print("Values:", records)

    con.executemany(sql, records)
    con.commit()

def folder_to_date(folder_name: str) -> datetime:
    """
    Convert 'dd.MM' folder name into datetime with current year.
    Example: '05.12' -> 2026-12-05
    """
    day, month = map(int, folder_name.split("."))
    year = datetime.now().year

    return datetime(year, month, day)

def sync_data_folder(
    conn: sqlite3.Connection,
    data_list: List[DeclareForm],
    db_path: str
) -> int:
    cursor = conn.cursor()
    # Insert data
    folder_name = Path(db_path).name

    folder_date = int(folder_to_date(folder_name).timestamp())
    cursor.execute("""
    INSERT INTO folder (name, origin_path, date)
        VALUES (?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            origin_path = excluded.origin_path,
            name = excluded.name
    """, (folder_name, db_path, folder_date))

    folder_id = cursor.execute(
        "SELECT id FROM folder WHERE date = ?",
        (folder_date,)
    ).fetchone()[0]
    print("Folder ID:", folder_id)
    try:
        cursor.executemany("""
            INSERT INTO declare_form (
                folder_id,
                nvl_code, bill, invoice, declare_code, type_code,
                route_type, term, date, tms, form_code, method, official_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(folder_id, nvl_code)
            DO UPDATE SET
                bill = excluded.bill,
                invoice = excluded.invoice,
                declare_code = excluded.declare_code,
                type_code = excluded.type_code,
                route_type = excluded.route_type,
                term = excluded.term,
                date = excluded.date,
                tms = excluded.tms,
                form_code = excluded.form_code,
                method = excluded.method,
                official_time = excluded.official_time
        """, [
            (
                folder_id,
                item.nvl_code,
                item.bill,
                item.invoice,
                item.declare_code,
                item.type_code,
                item.route_type,
                item.term,
                item.date,
                item.tms,
                item.form_code,
                item.method,
                item.time
            )
            for item in data_list
        ])
    except Exception as e:
        print("❌ EXECUTEMANY ERROR:", e)
        raise

    conn.commit()
    return folder_id


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

def clear_cells(con: sqlite3.Connection) -> None:
    with con:
        con.execute("DELETE FROM cell;")


