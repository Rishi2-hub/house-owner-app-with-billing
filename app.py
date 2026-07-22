"""
Ghar Saathi — House Owner Rental Management
A local, offline Streamlit app to manage floors, tenants, documents and monthly
bills (rent, water, electricity, dustbin) with both English (AD) and Nepali (BS)
calendars. All data lives on your own device storage.
"""

import os
import base64
import datetime

import streamlit as st

from lib import db
from lib import nepali_cal as cal
from lib import pdf_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANNER = os.path.join(BASE_DIR, "assets", "house_bg.png")

ID_TYPES = ["Citizenship", "License", "NID (National ID)", "Passport", "Other"]

st.set_page_config(
    page_title="Ghar Saathi — House Manager",
    page_icon="🏠",
    layout="wide",
)

db.init_db()


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------
def _img_b64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def inject_css():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem; max-width: 1200px;}
        .stApp {background-color: #f8faf9;}
        .gs-banner {
            border-radius: 16px; padding: 2rem 2.25rem; color: #ffffff;
            margin-bottom: 1.25rem;
            background-size: cover; background-position: center;
            box-shadow: 0 8px 24px rgba(15,118,110,0.18);
        }
        .gs-banner h1 {font-size: 2rem; margin: 0; font-weight: 700;
            text-shadow: 0 2px 12px rgba(0,0,0,0.55);}
        .gs-banner p {margin: .35rem 0 0; font-size: 1rem; opacity: .95;
            text-shadow: 0 2px 10px rgba(0,0,0,0.55);}
        .gs-datebar {display:flex; gap:.75rem; flex-wrap:wrap; margin-top:.9rem;}
        .gs-chip {background: rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35);
            padding:.35rem .85rem; border-radius:999px; font-size:.9rem; backdrop-filter: blur(4px);}
        .gs-card {background:#ffffff; border:1px solid #e2ede9; border-radius:14px;
            padding:1.1rem 1.25rem; box-shadow:0 2px 8px rgba(15,118,110,0.05);}
        .gs-metric {background:#ffffff; border:1px solid #e2ede9; border-radius:14px;
            padding:1rem 1.15rem; text-align:left;}
        .gs-metric .v {font-size:1.6rem; font-weight:700; color:#0f766e;}
        .gs-metric .l {font-size:.85rem; color:#5b716d; margin-top:.15rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def banner(title, subtitle):
    b64 = _img_b64(BANNER)
    grad = "linear-gradient(rgba(12,74,68,0.55), rgba(12,74,68,0.65))"
    if b64:
        bg = f"{grad}, url('data:image/png;base64,{b64}')"
    else:
        bg = "linear-gradient(135deg,#0f766e,#115e59)"
    eng, nep = cal.dual_today_label()
    st.markdown(
        f"""
        <div class="gs-banner" style="background-image:{bg};">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="gs-datebar">
                <span class="gs-chip">📅 English: {eng}</span>
                <span class="gs-chip">🗓️ Nepali: {nep}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(x):
    return f"Rs. {x:,.0f}"


def floor_options():
    floors = db.get_floors()
    return {f["name"]: f["id"] for f in floors}, floors


def format_pref_date(ad_date_str):
    """Format an ISO AD date string (e.g. tenant move-in date) according
    to the global BS/AD display preference chosen in the sidebar."""
    if not ad_date_str:
        return ""
    pref = st.session_state.get("date_pref", "BS")
    d = datetime.date.fromisoformat(ad_date_str)
    if pref == "BS":
        return cal.format_bs_date(d)
    return d.strftime("%d %B %Y")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def page_dashboard():
    banner(
        "Ghar Saathi",
        "Your rental house — floors, tenants & monthly bills in one place",
    )

    floors = db.get_floors()
    tenants = db.get_tenants()

    # Month selection
    st.markdown("### Select month")

    bs_year, bs_month, year, month = month_selector("dashboard")

    st.caption(
        f"Showing {cal.NEPALI_MONTHS[bs_month - 1]} {bs_year} BS · "
        f"{cal.english_month_label(year, month)}"
    )

    st.divider()

    # Get bills for selected month
    bills = db.get_bills_for_month(year, month)

    # Calculate selected month's totals
    total_billed = sum(
        db.bill_total(bill)
        for bill in bills
    )

    total_collected = sum(
        db.bill_amount_paid(bill)
        for bill in bills
    )

    total_due = sum(
        db.bill_due(bill)
        for bill in bills
    )

    total_advance = sum(
        bill.get("advance_amount") or 0
        for bill in bills
    )

    # Dashboard summary cards
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Floors",
        len(floors),
    )

    c2.metric(
        "Tenants",
        len(tenants),
    )

    c3.metric(
        "Collected",
        money(total_collected),
    )

    c4.metric(
        "Due",
        money(total_due),
    )

    c5.metric(
        "Advance",
        money(total_advance),
    )

    st.divider()

    # Selected month heading
    st.subheader(
        f"Bills · {cal.NEPALI_MONTHS[bs_month - 1]} {bs_year}"
    )

    st.caption(
        f"English month: {cal.english_month_label(year, month)}"
    )

    st.caption(
        f"Total payable for the selected month: {money(total_billed)}"
    )

    # Selected month's bills
    if bills:
        rows = []

        for bill in bills:
            rows.append({
                "Floor": bill.get("floor_name", ""),
                "Tenant": bill.get("tenant_name", ""),
                "Total Payable": money(
                    db.bill_total(bill)
                ),
                "Paid": money(
                    db.bill_amount_paid(bill)
                ),
                "Due": money(
                    db.bill_due(bill)
                ),
                "Advance": money(
                    bill.get("advance_amount") or 0
                ),
                "Status": db.bill_status(bill),
            })

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "No bills recorded for the selected month."
        )


# ---------------------------------------------------------------------------
# Floors
# ---------------------------------------------------------------------------
def page_floors():
    banner("Floors & Units", "Create and edit each floor or unit of your house")

    with st.expander("➕ Add a new floor / unit", expanded=False):
        with st.form("add_floor", clear_on_submit=True):
            name = st.text_input("Floor / Unit name *", placeholder="e.g. 1st Floor, Ground Floor Shop")
            desc = st.text_area("Description", placeholder="Rooms, facilities, size, etc.")
            bg = st.file_uploader("Background / photo of this floor", type=["png", "jpg", "jpeg"])
            if st.form_submit_button("Add floor", type="primary"):
                if not name.strip():
                    st.error("Floor name is required.")
                else:
                    path = db.save_upload(bg, "floor") if bg else None
                    db.add_floor(name.strip(), desc.strip(), path)
                    st.success(f"Added '{name}'.")
                    st.rerun()

    floors = db.get_floors()
    if not floors:
        st.info("No floors yet. Add your first one above.")
        return

    for f in floors:
        with st.container(border=True):
            cols = st.columns([1, 3])
            with cols[0]:
                if f["background"] and os.path.exists(f["background"]):
                    st.image(f["background"], use_container_width=True)
                else:
                    st.markdown("🏢")
            with cols[1]:
                st.markdown(f"### {f['name']}")
                if f["description"]:
                    st.write(f["description"])
                n_tenants = len(db.get_tenants(f["id"]))
                st.caption(f"{n_tenants} tenant(s)")

                with st.popover("Edit"):
                    with st.form(f"edit_floor_{f['id']}"):
                        n = st.text_input("Name", value=f["name"])
                        d = st.text_area("Description", value=f["description"] or "")
                        newbg = st.file_uploader(
                            "Replace background", type=["png", "jpg", "jpeg"],
                            key=f"bg_{f['id']}",
                        )
                        c1, c2 = st.columns(2)
                        if c1.form_submit_button("Save", type="primary"):
                            path = db.save_upload(newbg, "floor") if newbg else None
                            db.update_floor(f["id"], n.strip(), d.strip(), path)
                            st.success("Updated.")
                            st.rerun()
                        if c2.form_submit_button("Delete floor"):
                            db.delete_floor(f["id"])
                            st.warning("Floor deleted.")
                            st.rerun()


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------
def tenant_form(floors_map, existing=None, key="new"):
    """Render tenant add/edit form."""

    is_edit = existing is not None

    names = list(floors_map.keys())

    default_floor_idx = 0
    if is_edit:
        for i, (nm, fid) in enumerate(floors_map.items()):
            if fid == existing["floor_id"]:
                default_floor_idx = i
                break

    with st.form(f"tenant_form_{key}", clear_on_submit=not is_edit):

        c1, c2 = st.columns(2)

        floor_name = c1.selectbox(
            "Floor / Unit *",
            names,
            index=default_floor_idx,
        )

        name = c2.text_input(
            "Tenant Full Name *",
            value=existing["name"] if is_edit else "",
        )

        c3, c4 = st.columns(2)

        phone = c3.text_input(
            "Phone",
            value=existing["phone"] if is_edit else "",
        )

        email = c4.text_input(
            "Email",
            value=existing["email"] if is_edit else "",
        )

        c5, c6 = st.columns(2)

        id_type = c5.selectbox(
            "ID Type",
            ID_TYPES,
            index=ID_TYPES.index(existing["id_type"])
            if is_edit and existing["id_type"] in ID_TYPES
            else 0,
        )

        id_number = c6.text_input(
            "ID Number",
            value=existing["id_number"] if is_edit else "",
        )

        c7, c8 = st.columns(2)

        rent = c7.number_input(
            "Monthly Rent (Rs.)",
            min_value=0.0,
            step=500.0,
            value=float(existing["rent_amount"]) if is_edit else 0.0,
        )

        move_in = c8.date_input(
            "Move-in Date",
            value=datetime.date.fromisoformat(existing["move_in_date"])
            if is_edit and existing["move_in_date"]
            else cal.today_ad(),
        )

        # -------------------------
        # Multiple Photos
        # -------------------------

        photos = st.file_uploader(
            "Tenant Photos (Maximum 5)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"photos_{key}",
        )

        # -------------------------
        # Documents
        # -------------------------

        docs = st.file_uploader(
            "ID Documents",
            type=["png", "jpg", "jpeg", "pdf"],
            accept_multiple_files=True,
            key=f"docs_{key}",
        )

        notes = st.text_area(
            "Notes",
            value=existing["notes"] if is_edit else "",
        )

        submitted = st.form_submit_button(
            "Save Tenant" if is_edit else "Add Tenant",
            type="primary",
        )

        if submitted:

            if not name.strip():
                st.error("Tenant name is required.")
                return None

            data = {
                "floor_id": floors_map[floor_name],
                "name": name.strip(),
                "phone": phone.strip(),
                "email": email.strip(),
                "id_type": id_type,
                "id_number": id_number.strip(),
                "rent_amount": rent,
                "move_in_date": move_in.isoformat(),
                "notes": notes.strip(),
            }

            # -------------------------
            # Save Photos
            # -------------------------

            photo_paths = []

            if photos:
                for photo in photos[:5]:
                    path = db.save_upload(photo, "photo")
                    if path:
                        photo_paths.append(path)

            if is_edit:
                data["photos"] = existing["photos"] + photo_paths
            else:
                data["photos"] = photo_paths

            # -------------------------
            # Save Documents
            # -------------------------
            # "documents" is always set (even with no new uploads) so
            # db.update_tenant() never sees a missing key.

            saved_docs = []

            if docs:
                for doc in docs:
                    path = db.save_upload(doc, "doc")
                    if path:
                        saved_docs.append(path)

            if is_edit:
                data["documents"] = existing["documents"] + saved_docs
            else:
                data["documents"] = saved_docs

            return data

    return None


def page_tenants():
    banner(
        "Tenants",
        "Record everyone renting, with photos, ID documents and rent",
    )

    floors_map, floors = floor_options()

    if not floors_map:
        st.warning(
            "Please add at least one floor first from the Floors page."
        )
        return

    # -------------------------
    # Add Tenant
    # -------------------------

    with st.expander("➕ Add New Tenant", expanded=False):
        data = tenant_form(floors_map, key="new")

        if data:
            db.add_tenant(data)
            st.success(f"{data['name']} added successfully.")
            st.rerun()

    st.divider()

    # -------------------------
    # Filter
    # -------------------------

    floor_list = ["All Floors"] + list(floors_map.keys())

    selected_floor = st.selectbox(
        "Filter by Floor",
        floor_list,
    )

    if selected_floor == "All Floors":
        tenants = db.get_tenants()
    else:
        tenants = db.get_tenants(floors_map[selected_floor])

    if not tenants:
        st.info("No tenants found.")
        return

    floor_names = {
        f["id"]: f["name"]
        for f in floors
    }

    # -------------------------
    # Tenant Cards
    # -------------------------

    for t in tenants:

        with st.container(border=True):

            st.markdown(f"## 👤 {t['name']}")

            st.caption(
                f"🏠 {floor_names.get(t['floor_id'],'-')} | Monthly Rent: {money(t['rent_amount'])}"
            )

            info = []

            if t["phone"]:
                info.append(f"📞 {t['phone']}")

            if t["email"]:
                info.append(f"✉️ {t['email']}")

            if t["id_number"]:
                info.append(
                    f"🪪 {t['id_type']} : {t['id_number']}"
                )

            if t["move_in_date"]:
                info.append(
                    f"📅 Since {format_pref_date(t['move_in_date'])}"
                )

            if info:
                st.write(" | ".join(info))

            # -------------------------
            # Tenant Photos
            # -------------------------

            if t.get("photos"):
                st.markdown("### 📷 Tenant Photos")

                cols = st.columns(min(5, len(t["photos"])))

                for i, img in enumerate(t["photos"]):
                    if os.path.exists(img):
                        cols[i % 5].image(
                            img,
                            use_container_width=True,
                        )
            else:
                st.info("No photos uploaded.")

            # -------------------------
            # Documents
            # -------------------------

            if t["documents"]:

                with st.expander(
                    f"📄 Documents ({len(t['documents'])})"
                ):

                    dcols = st.columns(3)

                    for i, doc in enumerate(t["documents"]):

                        if not os.path.exists(doc):
                            continue

                        if doc.lower().endswith(
                            (".png", ".jpg", ".jpeg")
                        ):
                            dcols[i % 3].image(
                                doc,
                                use_container_width=True,
                            )
                        else:
                            dcols[i % 3].write(
                                "📄 " + os.path.basename(doc)
                            )

            # -------------------------
            # Notes
            # -------------------------

            if t["notes"]:
                st.markdown("### 📝 Notes")
                st.write(t["notes"])

            # -------------------------
            # Edit Tenant
            # -------------------------

            with st.popover("✏️ Edit Tenant"):

                updated = tenant_form(
                    floors_map,
                    existing=t,
                    key=f"edit_{t['id']}",
                )

                if updated:

                    db.update_tenant(
                        t["id"],
                        updated,
                    )

                    st.success("Tenant updated successfully.")

                    st.rerun()

                if st.button(
                    "🗑 Delete Tenant",
                    key=f"delete_{t['id']}",
                    type="secondary",
                ):

                    db.delete_tenant(t["id"])

                    st.warning("Tenant deleted.")

                    st.rerun()


# ---------------------------------------------------------------------------
# Monthly bills
# ---------------------------------------------------------------------------
def month_selector(key_prefix):
    """
    Select Nepali (BS) year and month.

    By default, the previous completed Nepali month is selected because
    monthly bills are prepared after the month has ended.

    Returns:
        bs_year, bs_month, ad_year, ad_month
    """

    today_bs = cal.current_bs()

    # Select previous completed Nepali month by default
    if today_bs.month == 1:
        default_bs_year = today_bs.year - 1
        default_bs_month = 12
    else:
        default_bs_year = today_bs.year
        default_bs_month = today_bs.month - 1

    years = list(
        range(today_bs.year - 3, today_bs.year + 3)
    )

    default_year_index = years.index(default_bs_year)

    c1, c2 = st.columns(2)

    bs_year = c1.selectbox(
        "Year (BS)",
        years,
        index=default_year_index,
        key=f"{key_prefix}_year",
    )

    bs_month = c2.selectbox(
        "Month (BS)",
        list(range(1, 13)),
        format_func=lambda selected_month: (
            cal.NEPALI_MONTHS[selected_month - 1]
        ),
        index=default_bs_month - 1,
        key=f"{key_prefix}_month",
    )

    year, month = cal.ad_month_from_bs(
        bs_year,
        bs_month,
    )

    return bs_year, bs_month, year, month


def page_bills():
    banner("Monthly Bills", "Rent, water, metered electricity, payments and outstanding dues")

    tenants = db.get_tenants()
    if not tenants:
        st.warning("Add floors and tenants first.")
        return

    bs_year, bs_month, year, month = month_selector("bills")
    st.divider()

    tenant_map = {f"{t['name']}": t for t in tenants}
    picked = st.selectbox("Select tenant to enter / edit this month's bill", list(tenant_map.keys()))
    tenant = tenant_map[picked]

    existing = db.get_bill(tenant["id"], year, month)

    st.markdown(
        f"**Bill for {tenant['name']} — {cal.english_month_label(year, month)}**"
    )
    st.caption(f"Nepali Month : {cal.NEPALI_MONTHS[bs_month-1]} {bs_year}")

    with st.form("bill_form"):

        c1, c2, c3 = st.columns(3)
        rent = c1.number_input(
            "Rent (Rs.)", min_value=0.0, step=500.0,
            value=float(existing["rent_amount"]) if existing else float(tenant["rent_amount"]),
        )
        dustbin = c2.number_input(
            "Dustbin / waste (Rs.)", min_value=0.0, step=50.0,
            value=float(existing["dustbin_amount"]) if existing else 0.0,
        )
        other = c3.number_input(
            "Other charges (Rs.)", min_value=0.0, step=50.0,
            value=float(existing["other_amount"]) if existing else 0.0,
        )

        legacy_water = db.water_charge(existing) if existing else 0.0
        water_amount = st.number_input(
            "Water price (Rs.)", min_value=0.0, step=50.0,
            value=float(legacy_water),
        )

        st.markdown("**Electricity**")
        e1, e2, e3 = st.columns(3)
        previous_reading = e1.number_input(
            "Previous meter reading", min_value=0.0, step=1.0,
            value=float(existing.get("previous_meter_reading", 0)) if existing else 0.0,
        )
        current_reading = e2.number_input(
            "Current meter reading", min_value=0.0, step=1.0,
            value=float(existing.get("current_meter_reading", existing.get("electricity_units", 0))) if existing else 0.0,
        )
        elec_rate = e3.number_input(
            "Rate per electricity unit (Rs.)", min_value=0.0, step=1.0,
            value=float(existing["electricity_rate"]) if existing else 0.0,
        )
        elec_units = max(0.0, current_reading - previous_reading)
        st.caption(f"Total units used this month: {elec_units:,.0f}")

        st.markdown("**Payment details**")
        p1, p2, p3 = st.columns(3)
        advance_amount = p1.number_input(
            "Advance amount (Rs.)", min_value=0.0, step=100.0,
            value=float(existing.get("advance_amount", 0)) if existing else 0.0,
        )
        past_due_amount = p2.number_input(
            "Past months' due amount (Rs.)", min_value=0.0, step=100.0,
            value=float(existing.get("past_due_amount", 0)) if existing else 0.0,
        )
        default_paid = db.bill_amount_paid(existing) if existing else 0.0
        amount_paid = p3.number_input(
            "Total amount paid by customer (Rs.)", min_value=0.0, step=100.0,
            value=float(default_paid),
        )

        other_desc = st.text_input(
            "Other charges description",
            value=existing["other_desc"] if existing and existing["other_desc"] else "",
        )
        current_charges = rent + water_amount + elec_units * elec_rate + dustbin + other
        preview_total = max(0.0, current_charges + past_due_amount - advance_amount)
        remaining_due = max(0.0, preview_total - amount_paid)
        customer_credit = max(0.0, amount_paid - preview_total)
        st.info(
            f"Current charges: **{money(current_charges)}**  |  "
            f"Total payable: **{money(preview_total)}**  |  "
            f"Remaining due: **{money(remaining_due)}**"
        )
        if customer_credit:
            st.success(f"Extra customer credit: **{money(customer_credit)}**")

        if st.form_submit_button("Save bill", type="primary"):
            if current_reading < previous_reading:
                st.error("Current meter reading cannot be lower than the previous reading.")
            else:
                db.upsert_bill({
                    "tenant_id": tenant["id"], "year_ad": year, "month_ad": month,
                    "bs_year": bs_year, "bs_month": bs_month,
                    "rent_amount": rent, "water_amount": water_amount,
                    "previous_meter_reading": previous_reading,
                    "current_meter_reading": current_reading,
                    "electricity_units": elec_units, "electricity_rate": elec_rate,
                    "dustbin_amount": dustbin, "other_amount": other,
                    "other_desc": other_desc,
                    "advance_amount": advance_amount,
                    "past_due_amount": past_due_amount,
                    "amount_paid": amount_paid,
                    "paid": amount_paid >= preview_total,
                })
                st.success("Bill saved.")
                st.rerun()

    if existing:
        floor_nm = next(
            (f["name"] for f in db.get_floors() if f["id"] == tenant["floor_id"]), ""
        )
        pdf_bytes = pdf_report.generate_bill_receipt(
            existing, tenant, floor_nm, db.bill_total(existing)
        )
        st.download_button(
            "⬇️ Download PDF receipt for this tenant",
            data=pdf_bytes,
            file_name=f"receipt_{tenant['name'].replace(' ', '_')}_{year}_{month:02d}.pdf",
            mime="application/pdf",
        )

    st.divider()
    st.subheader(f"All Bills • {cal.NEPALI_MONTHS[bs_month-1]} {bs_year}")
    st.caption(f"English : {cal.english_month_label(year, month)}")

    bills = db.get_bills_for_month(year, month)
    if not bills:
        st.info("No bills recorded for this month yet.")
        return

    rows = []
    grand = 0.0
    for b in bills:
        total = db.bill_total(b)
        grand += total
        rows.append({
            "Floor": b["floor_name"],
            "Tenant": b["tenant_name"],
            "Rent": b["rent_amount"],
            "Water": db.water_charge(b),
            "Meter Units": b.get("electricity_units", 0),
            "Electricity": (b.get("electricity_units") or 0) * (b.get("electricity_rate") or 0),
            "Dustbin": b["dustbin_amount"],
            "Other": b["other_amount"],
            "Past Due": b.get("past_due_amount", 0),
            "Advance": b.get("advance_amount", 0),
            "Total Payable": total,
            "Paid": db.bill_amount_paid(b),
            "Remaining Due": db.bill_due(b),
            "Status": db.bill_status(b),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.metric("Grand total for the month", money(grand))

    with st.expander("⬇️ Download individual PDF receipts"):
        tenants_by_id = {t["id"]: t for t in tenants}
        rcols = st.columns(2)
        for idx, b in enumerate(bills):
            t = tenants_by_id.get(b["tenant_id"])
            if not t:
                continue
            pdf_bytes = pdf_report.generate_bill_receipt(
                b, t, b["floor_name"], db.bill_total(b)
            )
            rcols[idx % 2].download_button(
                f"{b['tenant_name']} — {money(db.bill_total(b))}",
                data=pdf_bytes,
                file_name=f"receipt_{t['name'].replace(' ','_')}_{bs_year}_{bs_month}.pdf",
                mime="application/pdf",
                key=f"rcpt_{b['id']}",
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Yearly income summary
# ---------------------------------------------------------------------------
def page_year_summary():

    banner(
        "Yearly Summary",
        "Income summary by Nepali year",
    )

    today_bs = cal.ad_to_bs(cal.today_ad())

    years = list(range(today_bs.year-3, today_bs.year+3))

    year = st.selectbox(
        "Nepali Year",
        years,
        index=3,
    )

    bills = db.get_bills_for_year(year)

    total = 0
    collected = 0

    rows = []

    for month in range(1, 13):

        month_bills = [
            b for b in bills
            if b["month_ad"] == month
        ]

        billed = sum(db.bill_total(b) for b in month_bills)

        paid = sum(db.bill_amount_paid(b) for b in month_bills)
        due = sum(db.bill_due(b) for b in month_bills)

        total += billed
        collected += paid

        rows.append({
            "Month": cal.NEPALI_MONTHS[month-1],
            "Billed": money(billed),
            "Collected": money(paid),
            "Due": money(due)
        })

    st.dataframe(rows, use_container_width=True)

    st.metric("Total Billed", money(total))
    st.metric("Collected", money(collected))
    st.metric("Due", money(total-collected))


# ---------------------------------------------------------------------------
# Calendar view
# ---------------------------------------------------------------------------
def page_calendar():

    banner(
        "Nepali Calendar",
        "View Nepali Calendar",
    )

    bs_today = cal.ad_to_bs(cal.today_ad())

    year = st.selectbox(
        "Year",
        range(bs_today.year-2, bs_today.year+3),
        index=2,
    )

    month = st.selectbox(
        "Month",
        range(1, 13),
        format_func=lambda x: cal.NEPALI_MONTHS[x-1],
        index=bs_today.month-1,
    )

    st.subheader(
        f"{cal.NEPALI_MONTHS[month-1]} {year}"
    )

    st.info(
        "Nepali Calendar support is enabled.\n\n"
        "Bills now use Nepali Year and Nepali Month."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()
    with st.sidebar:
        st.markdown("## 🏠 Ghar Saathi")
        st.caption("House Owner Manager")
        page = st.radio(
            "Go to",
            ["Dashboard", "Floors", "Tenants", "Monthly Bills", "Yearly Summary", "Calendar"],
            label_visibility="collapsed",
        )
        st.divider()

        st.session_state.setdefault("date_pref", "BS")
        pref = st.radio(
            "Date format",
            ["BS", "AD"],
            index=0 if st.session_state["date_pref"] == "BS" else 1,
            horizontal=True,
            key="date_pref_radio",
        )
        st.session_state["date_pref"] = pref

        st.divider()
        eng, nep = cal.dual_today_label()
        st.caption(f"📅 {eng}")
        st.caption(f"🗓️ {nep}")

    if page == "Dashboard":
        page_dashboard()
    elif page == "Floors":
        page_floors()
    elif page == "Tenants":
        page_tenants()
    elif page == "Monthly Bills":
        page_bills()
    elif page == "Yearly Summary":
        page_year_summary()
    elif page == "Calendar":
        page_calendar()


if __name__ == "__main__":
    main()
