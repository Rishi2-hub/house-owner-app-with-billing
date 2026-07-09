"""
Firestore data layer for the House Owner rental app (floors, tenants, bills),
with tenant photos and documents saved to LOCAL disk instead of Firebase
Storage — this avoids requiring the paid Blaze plan.

Trade-off: on Streamlit Community Cloud, uploaded photos/documents will
still be lost on app restart, since Cloud's filesystem is ephemeral. If you
mainly run this app on your own PC, local files persist normally there.
If you later want photos/documents to survive Cloud restarts too, upgrade
to the Blaze plan and swap save_upload() back to Firebase Storage.

Requires a Firebase service account configured in Streamlit secrets under
the [firebase] section (see secrets.toml.example). storage_bucket is no
longer required/used in this version.
"""

import os
import uuid
import datetime

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore


# ---------------------------------------------------------------------------
# Local upload folder (same layout as the original SQLite version)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Firebase init (runs once per app session, cached across reruns)
# ---------------------------------------------------------------------------
@st.cache_resource
def _init_firebase():
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        cred_dict.pop("storage_bucket", None)  # not needed in this version
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()


db_client = _init_firebase()


def init_db():
    """No-op: Firestore has no schema to create up front."""
    pass


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# File upload -> local disk (unchanged from the original SQLite version)
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


# ---------------------------------------------------------------------------
# Floors
# ---------------------------------------------------------------------------
def add_floor(name, description, background):
    doc_ref = db_client.collection("floors").document()
    doc_ref.set({
        "name": name,
        "description": description,
        "background": background,
        "created_at": _now(),
    })
    return doc_ref.id


def update_floor(floor_id, name, description, background=None):
    data = {"name": name, "description": description}
    if background is not None:
        data["background"] = background
    db_client.collection("floors").document(floor_id).update(data)


def delete_floor(floor_id):
    # Cascade: remove tenants (and their bills) on this floor first.
    tenants = db_client.collection("tenants").where("floor_id", "==", floor_id).stream()
    for t in tenants:
        delete_tenant(t.id)
    db_client.collection("floors").document(floor_id).delete()


def get_floors():
    docs = db_client.collection("floors").order_by("created_at").stream()
    result = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        result.append(row)
    return result


def get_floor(floor_id):
    doc = db_client.collection("floors").document(floor_id).get()
    if not doc.exists:
        return None
    row = doc.to_dict()
    row["id"] = doc.id
    return row


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------
def add_tenant(data):
    doc_ref = db_client.collection("tenants").document()
    doc_ref.set({
        "floor_id": data["floor_id"],
        "name": data["name"],
        "phone": data.get("phone"),
        "email": data.get("email"),
        "id_type": data.get("id_type"),
        "id_number": data.get("id_number"),
        "rent_amount": data.get("rent_amount", 0),
        "photos": data.get("photos", []),
        "documents": data.get("documents", []),
        "move_in_date": data.get("move_in_date"),
        "notes": data.get("notes"),
        "created_at": _now(),
    })
    return doc_ref.id


def update_tenant(tenant_id, data):
    existing = get_tenant(tenant_id)

    # Keep old photos/documents if the caller didn't provide new ones
    photos = data.get("photos")
    if photos is None:
        photos = existing["photos"]

    docs = data.get("documents")
    if docs is None:
        docs = existing["documents"]

    db_client.collection("tenants").document(tenant_id).update({
        "floor_id": data["floor_id"],
        "name": data["name"],
        "phone": data.get("phone"),
        "email": data.get("email"),
        "id_type": data.get("id_type"),
        "id_number": data.get("id_number"),
        "rent_amount": data.get("rent_amount", 0),
        "photos": photos,
        "documents": docs,
        "move_in_date": data.get("move_in_date"),
        "notes": data.get("notes"),
    })


def delete_tenant(tenant_id):
    bills = db_client.collection("bills").where("tenant_id", "==", tenant_id).stream()
    for b in bills:
        b.reference.delete()
    db_client.collection("tenants").document(tenant_id).delete()


def get_tenants(floor_id=None):
    coll = db_client.collection("tenants")
    if floor_id:
        docs = coll.where("floor_id", "==", floor_id).order_by("name").stream()
    else:
        docs = coll.order_by("name").stream()

    result = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        row.setdefault("photos", [])
        row.setdefault("documents", [])
        result.append(row)
    return result


def get_tenant(tenant_id):
    doc = db_client.collection("tenants").document(tenant_id).get()
    if not doc.exists:
        return None
    row = doc.to_dict()
    row["id"] = doc.id
    row.setdefault("photos", [])
    row.setdefault("documents", [])
    return row


# ---------------------------------------------------------------------------
# Bills
# Document ID = "{tenant_id}_{year_ad}_{month_ad}" — enforces one bill per
# tenant per month, equivalent to the old SQL UNIQUE constraint.
# ---------------------------------------------------------------------------
def _bill_doc_id(tenant_id, year_ad, month_ad):
    return f"{tenant_id}_{year_ad}_{month_ad}"


def upsert_bill(data):
    doc_id = _bill_doc_id(data["tenant_id"], data["year_ad"], data["month_ad"])
    db_client.collection("bills").document(doc_id).set({
        "tenant_id": data["tenant_id"],
        "year_ad": data["year_ad"],
        "month_ad": data["month_ad"],
        "rent_amount": data.get("rent_amount", 0),
        "water_units": data.get("water_units", 0),
        "water_rate": data.get("water_rate", 0),
        "electricity_units": data.get("electricity_units", 0),
        "electricity_rate": data.get("electricity_rate", 0),
        "dustbin_amount": data.get("dustbin_amount", 0),
        "other_amount": data.get("other_amount", 0),
        "other_desc": data.get("other_desc"),
        "paid": 1 if data.get("paid") else 0,
        "created_at": _now(),
    }, merge=True)


def set_bill_paid(bill_id, paid):
    db_client.collection("bills").document(bill_id).update({"paid": 1 if paid else 0})


def delete_bill(bill_id):
    db_client.collection("bills").document(bill_id).delete()


def get_bill(tenant_id, year_ad, month_ad):
    doc_id = _bill_doc_id(tenant_id, year_ad, month_ad)
    doc = db_client.collection("bills").document(doc_id).get()
    if not doc.exists:
        return None
    row = doc.to_dict()
    row["id"] = doc.id
    return row


def _attach_tenant_floor_info(bill_row, tenants_by_id, floors_by_id):
    t = tenants_by_id.get(bill_row["tenant_id"])
    if t:
        bill_row["tenant_name"] = t["name"]
        bill_row["floor_id"] = t["floor_id"]
        f = floors_by_id.get(t["floor_id"])
        bill_row["floor_name"] = f["name"] if f else ""
    else:
        bill_row["tenant_name"] = "(deleted tenant)"
        bill_row["floor_name"] = ""
    return bill_row


def get_bills_for_month(year_ad, month_ad):
    docs = (
        db_client.collection("bills")
        .where("year_ad", "==", year_ad)
        .where("month_ad", "==", month_ad)
        .stream()
    )

    tenants_by_id = {t["id"]: t for t in get_tenants()}
    floors_by_id = {f["id"]: f for f in get_floors()}

    rows = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        rows.append(_attach_tenant_floor_info(row, tenants_by_id, floors_by_id))

    rows.sort(key=lambda r: (r.get("floor_id") or "", r.get("tenant_name") or ""))
    return rows


def get_bills_for_year(year_ad):
    docs = db_client.collection("bills").where("year_ad", "==", year_ad).stream()

    tenants_by_id = {t["id"]: t for t in get_tenants()}
    floors_by_id = {f["id"]: f for f in get_floors()}

    rows = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        rows.append(_attach_tenant_floor_info(row, tenants_by_id, floors_by_id))

    rows.sort(key=lambda r: (r.get("month_ad", 0), r.get("floor_id") or "", r.get("tenant_name") or ""))
    return rows


def get_bills_for_tenant(tenant_id):
    docs = db_client.collection("bills").where("tenant_id", "==", tenant_id).stream()
    rows = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        rows.append(row)
    rows.sort(key=lambda r: (r["year_ad"], r["month_ad"]), reverse=True)
    return rows


def bill_total(bill):
    """Calculate total bill amount."""
    if bill is None:
        return 0.0
    return (
        (bill.get("rent_amount") or 0)
        + (bill.get("water_units") or 0) * (bill.get("water_rate") or 0)
        + (bill.get("electricity_units") or 0) * (bill.get("electricity_rate") or 0)
        + (bill.get("dustbin_amount") or 0)
        + (bill.get("other_amount") or 0)
    )