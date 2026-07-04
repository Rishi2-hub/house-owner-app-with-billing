"""
SQLite data layer for the House Owner rental management app.

All data is stored locally in a single SQLite file (data/house.db) and all
uploaded images/documents are stored on local disk (data/uploads/...).
"""

import os
import json
import sqlite3
import datetime
import uuid
from contextlib import contextmanager

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "house.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not exist yet."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS floors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                background TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                floor_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                id_type TEXT,
                id_number TEXT,
                rent_amount REAL DEFAULT 0,

                -- JSON list of tenant photos
                photo TEXT,

                -- JSON list of documents
                documents TEXT,

                move_in_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,

                FOREIGN KEY (floor_id)
                REFERENCES floors(id)
                ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,

                year_ad INTEGER NOT NULL,
                month_ad INTEGER NOT NULL,

                rent_amount REAL DEFAULT 0,

                water_units REAL DEFAULT 0,
                water_rate REAL DEFAULT 0,

                electricity_units REAL DEFAULT 0,
                electricity_rate REAL DEFAULT 0,

                dustbin_amount REAL DEFAULT 0,

                other_amount REAL DEFAULT 0,
                other_desc TEXT,

                paid INTEGER DEFAULT 0,

                created_at TEXT NOT NULL,

                FOREIGN KEY (tenant_id)
                REFERENCES tenants(id)
                ON DELETE CASCADE,

                UNIQUE(tenant_id, year_ad, month_ad)
            );
            """
        )


# ---------------------------------------------------------------------------
# File Upload
# ---------------------------------------------------------------------------

def save_upload(uploaded_file, prefix="file"):
    if uploaded_file is None:
        return None

    ext = os.path.splitext(uploaded_file.name)[1].lower() or ".png"

    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return filepath


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Floors
# ---------------------------------------------------------------------------

def add_floor(name, description, background):
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO floors
            (name, description, background, created_at)
            VALUES (?,?,?,?)
            """,
            (
                name,
                description,
                background,
                _now(),
            ),
        )
        return cur.lastrowid


def update_floor(floor_id, name, description, background=None):
    with get_conn() as conn:

        if background is not None:
            conn.execute(
                """
                UPDATE floors
                SET name=?, description=?, background=?
                WHERE id=?
                """,
                (
                    name,
                    description,
                    background,
                    floor_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE floors
                SET name=?, description=?
                WHERE id=?
                """,
                (
                    name,
                    description,
                    floor_id,
                ),
            )


def delete_floor(floor_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM floors WHERE id=?",
            (floor_id,),
        )


def get_floors():
    with get_conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM floors ORDER BY id"
            )
        ]


def get_floor(floor_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM floors WHERE id=?",
            (floor_id,),
        ).fetchone()

        return dict(row) if row else None
    
# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------

def add_tenant(data):
    """Add a new tenant."""

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tenants
            (
                floor_id,
                name,
                phone,
                email,
                id_type,
                id_number,
                rent_amount,
                photo,
                documents,
                move_in_date,
                notes,
                created_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                data["floor_id"],
                data["name"],
                data.get("phone"),
                data.get("email"),
                data.get("id_type"),
                data.get("id_number"),
                data.get("rent_amount", 0),

                # Store multiple photos as JSON
                json.dumps(data.get("photos", [])),

                json.dumps(data.get("documents", [])),

                data.get("move_in_date"),
                data.get("notes"),

                _now(),
            ),
        )

        return cur.lastrowid


def update_tenant(tenant_id, data):
    """Update tenant information."""

    existing = get_tenant(tenant_id)

    # Keep old photos if user didn't upload new ones
    photos = data.get("photos")
    if photos is None:
        photos = existing["photos"]

    # Keep old documents if user didn't upload new ones
    docs = data.get("documents")
    if docs is None:
        docs = existing["documents"]

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tenants
            SET
                floor_id=?,
                name=?,
                phone=?,
                email=?,
                id_type=?,
                id_number=?,
                rent_amount=?,
                photo=?,
                documents=?,
                move_in_date=?,
                notes=?
            WHERE id=?
            """,
            (
                data["floor_id"],
                data["name"],
                data.get("phone"),
                data.get("email"),
                data.get("id_type"),
                data.get("id_number"),
                data.get("rent_amount", 0),

                json.dumps(photos),

                json.dumps(docs),

                data.get("move_in_date"),
                data.get("notes"),

                tenant_id,
            ),
        )


def delete_tenant(tenant_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM tenants WHERE id=?",
            (tenant_id,),
        )


def _tenant_row(row):
    """Convert database row into dictionary."""

    d = dict(row)

    # Read tenant photos
    try:
        d["photos"] = json.loads(d.get("photo") or "[]")
    except Exception:
        d["photos"] = []

    # Backward compatibility
    if not d["photos"] and d.get("photo"):
        d["photos"] = [d["photo"]]

    # Read documents
    try:
        d["documents"] = json.loads(d.get("documents") or "[]")
    except Exception:
        d["documents"] = []

    return d


def get_tenants(floor_id=None):
    with get_conn() as conn:

        if floor_id:
            rows = conn.execute(
                """
                SELECT *
                FROM tenants
                WHERE floor_id=?
                ORDER BY name
                """,
                (floor_id,),
            )
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM tenants
                ORDER BY name
                """
            )

        return [_tenant_row(r) for r in rows]


def get_tenant(tenant_id):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM tenants
            WHERE id=?
            """,
            (tenant_id,),
        ).fetchone()

        return _tenant_row(row) if row else None
# ---------------------------------------------------------------------------
# Bills
# ---------------------------------------------------------------------------

def upsert_bill(data):
    """Insert or update a monthly bill."""

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO bills
            (
                tenant_id,
                year_ad,
                month_ad,
                rent_amount,
                water_units,
                water_rate,
                electricity_units,
                electricity_rate,
                dustbin_amount,
                other_amount,
                other_desc,
                paid,
                created_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)

            ON CONFLICT(tenant_id, year_ad, month_ad)

            DO UPDATE SET

                rent_amount=excluded.rent_amount,
                water_units=excluded.water_units,
                water_rate=excluded.water_rate,
                electricity_units=excluded.electricity_units,
                electricity_rate=excluded.electricity_rate,
                dustbin_amount=excluded.dustbin_amount,
                other_amount=excluded.other_amount,
                other_desc=excluded.other_desc,
                paid=excluded.paid
            """,
            (
                data["tenant_id"],
                data["year_ad"],
                data["month_ad"],

                data.get("rent_amount", 0),

                data.get("water_units", 0),
                data.get("water_rate", 0),

                data.get("electricity_units", 0),
                data.get("electricity_rate", 0),

                data.get("dustbin_amount", 0),

                data.get("other_amount", 0),
                data.get("other_desc"),

                1 if data.get("paid") else 0,

                _now(),
            ),
        )


def set_bill_paid(bill_id, paid):
    with get_conn() as conn:
        conn.execute(
            "UPDATE bills SET paid=? WHERE id=?",
            (
                1 if paid else 0,
                bill_id,
            ),
        )


def delete_bill(bill_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM bills WHERE id=?",
            (bill_id,),
        )


def get_bill(tenant_id, year_ad, month_ad):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM bills
            WHERE tenant_id=?
            AND year_ad=?
            AND month_ad=?
            """,
            (
                tenant_id,
                year_ad,
                month_ad,
            ),
        ).fetchone()

        return dict(row) if row else None


def get_bills_for_month(year_ad, month_ad):
    """Return all bills for one month."""

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                b.*,
                t.name AS tenant_name,
                t.floor_id,
                f.name AS floor_name

            FROM bills b

            JOIN tenants t
                ON t.id=b.tenant_id

            JOIN floors f
                ON f.id=t.floor_id

            WHERE
                b.year_ad=?
                AND
                b.month_ad=?

            ORDER BY
                f.id,
                t.name
            """,
            (
                year_ad,
                month_ad,
            ),
        )

        return [dict(r) for r in rows]


def get_bills_for_year(year_ad):
    """Return all bills for one year."""

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                b.*,
                t.name AS tenant_name,
                t.floor_id,
                f.name AS floor_name

            FROM bills b

            JOIN tenants t
                ON t.id=b.tenant_id

            JOIN floors f
                ON f.id=t.floor_id

            WHERE
                b.year_ad=?

            ORDER BY
                b.month_ad,
                f.id,
                t.name
            """,
            (year_ad,),
        )

        return [dict(r) for r in rows]


def get_bills_for_tenant(tenant_id):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM bills
            WHERE tenant_id=?
            ORDER BY
                year_ad DESC,
                month_ad DESC
            """,
            (tenant_id,),
        )

        return [dict(r) for r in rows]


def bill_total(bill):
    """Calculate total bill amount."""

    if bill is None:
        return 0.0

    return (
        (bill["rent_amount"] or 0)
        + (bill["water_units"] or 0) * (bill["water_rate"] or 0)
        + (bill["electricity_units"] or 0) * (bill["electricity_rate"] or 0)
        + (bill["dustbin_amount"] or 0)
        + (bill["other_amount"] or 0)
    )