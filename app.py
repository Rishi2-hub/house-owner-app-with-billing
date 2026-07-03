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


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def page_dashboard():
    banner("Ghar Saathi", "Your rental house — floors, tenants & monthly bills in one place")

    floors = db.get_floors()
    tenants = db.get_tenants()

    today = cal.today_ad()
    bills = db.get_bills_for_month(today.year, today.month)
    total_billed = sum(db.bill_total(b) for b in bills)
    total_collected = sum(db.bill_total(b) for b in bills if b["paid"])
    total_due = total_billed - total_collected

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, len(floors), "Floors / Units"),
        (c2, len(tenants), "Tenants"),
        (c3, money(total_collected), "Collected this month"),
        (c4, money(total_due), "Due this month"),
    ]:
        col.markdown(
            f"<div class='gs-metric'><div class='v'>{val}</div><div class='l'>{label}</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader(f"This month · {cal.english_month_label(today.year, today.month)}")
    st.caption(f"Nepali: {cal.nepali_month_label_for(today.year, today.month)}")

    if not floors:
        st.info("Start by adding a floor/unit from the **Floors** section in the sidebar.")
        return
    if not tenants:
        st.info("Add tenants from the **Tenants** section to begin tracking bills.")
        return

    if bills:
        rows = []
        for b in bills:
            rows.append({
                "Floor": b["floor_name"],
                "Tenant": b["tenant_name"],
                "Total": db.bill_total(b),
                "Status": "Paid" if b["paid"] else "Due",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No bills generated for this month yet. Go to **Monthly Bills** to add them.")


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
    """Render a tenant form. Returns dict of values + files or None."""
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
        floor_name = c1.selectbox("Floor / Unit *", names, index=default_floor_idx)
        name = c2.text_input("Tenant full name *", value=existing["name"] if is_edit else "")

        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone", value=existing["phone"] if is_edit else "")
        email = c4.text_input("Email", value=existing["email"] if is_edit else "")

        c5, c6 = st.columns(2)
        id_type = c5.selectbox(
            "ID type", ID_TYPES,
            index=ID_TYPES.index(existing["id_type"]) if is_edit and existing["id_type"] in ID_TYPES else 0,
        )
        id_number = c6.text_input("ID number", value=existing["id_number"] if is_edit else "")

        c7, c8 = st.columns(2)
        rent = c7.number_input(
            "Monthly rent (Rs.)", min_value=0.0, step=500.0,
            value=float(existing["rent_amount"]) if is_edit else 0.0,
        )
        move_in = c8.date_input(
            "Move-in date",
            value=datetime.date.fromisoformat(existing["move_in_date"])
            if is_edit and existing["move_in_date"] else cal.today_ad(),
        )

        photo = st.file_uploader("Profile photo", type=["png", "jpg", "jpeg"], key=f"photo_{key}")
        docs = st.file_uploader(
            "ID documents (citizenship / license / NID scans) — you can select multiple",
            type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, key=f"docs_{key}",
        )
        notes = st.text_area("Notes", value=existing["notes"] if is_edit else "")

        submitted = st.form_submit_button("Save tenant" if is_edit else "Add tenant", type="primary")
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
            if photo:
                data["photo"] = db.save_upload(photo, "photo")
            if docs:
                saved = [db.save_upload(d, "doc") for d in docs]
                if is_edit:
                    data["documents"] = existing["documents"] + saved
                else:
                    data["documents"] = saved
            return data
    return None


def page_tenants():
    banner("Tenants", "Record everyone renting, with photo, ID documents and rent")

    floors_map, floors = floor_options()
    if not floors_map:
        st.warning("Please add at least one floor first (see the **Floors** section).")
        return

    with st.expander("➕ Add a new tenant", expanded=False):
        data = tenant_form(floors_map, key="new")
        if data:
            db.add_tenant(data)
            st.success(f"Added tenant '{data['name']}'.")
            st.rerun()

    # Filter
    filter_names = ["All floors"] + list(floors_map.keys())
    picked = st.selectbox("Filter by floor", filter_names)
    floor_filter = None if picked == "All floors" else floors_map[picked]

    tenants = db.get_tenants(floor_filter)
    if not tenants:
        st.info("No tenants yet.")
        return

    floor_names = {f["id"]: f["name"] for f in floors}
    for t in tenants:
        with st.container(border=True):
            cols = st.columns([1, 3])
            with cols[0]:
                if t["photo"] and os.path.exists(t["photo"]):
                    st.image(t["photo"], use_container_width=True)
                else:
                    st.markdown("### 👤")
            with cols[1]:
                st.markdown(f"### {t['name']}")
                st.caption(f"{floor_names.get(t['floor_id'], '—')} · Rent {money(t['rent_amount'])}")
                info = []
                if t["phone"]:
                    info.append(f"📞 {t['phone']}")
                if t["id_type"] and t["id_number"]:
                    info.append(f"🪪 {t['id_type']}: {t['id_number']}")
                if t["move_in_date"]:
                    info.append(f"🗝️ Since {t['move_in_date']}")
                if info:
                    st.write(" · ".join(info))
                if t["notes"]:
                    st.write(t["notes"])

                if t["documents"]:
                    with st.expander(f"📎 Documents ({len(t['documents'])})"):
                        dcols = st.columns(3)
                        for i, dpath in enumerate(t["documents"]):
                            if os.path.exists(dpath) and dpath.lower().endswith((".png", ".jpg", ".jpeg")):
                                dcols[i % 3].image(dpath, use_container_width=True)
                            elif os.path.exists(dpath):
                                dcols[i % 3].write(f"📄 {os.path.basename(dpath)}")

                with st.popover("Edit tenant"):
                    edata = tenant_form(floors_map, existing=t, key=f"edit_{t['id']}")
                    if edata:
                        db.update_tenant(t["id"], edata)
                        st.success("Tenant updated.")
                        st.rerun()
                    if st.button("Delete tenant", key=f"del_{t['id']}"):
                        db.delete_tenant(t["id"])
                        st.warning("Tenant deleted.")
                        st.rerun()


# ---------------------------------------------------------------------------
# Monthly bills
# ---------------------------------------------------------------------------
def month_selector(key_prefix):
    today = cal.today_ad()
    years = list(range(today.year - 3, today.year + 2))
    c1, c2 = st.columns(2)
    year = c1.selectbox(
        "Year (AD)", years, index=years.index(today.year), key=f"{key_prefix}_y"
    )
    month = c2.selectbox(
        "Month (English)", list(range(1, 13)),
        format_func=lambda m: cal.ENGLISH_MONTHS[m - 1],
        index=today.month - 1, key=f"{key_prefix}_m",
    )
    st.caption(
        f"🗓️ Nepali month: **{cal.nepali_month_label_for(year, month)}** "
        f"· English: **{cal.english_month_label(year, month)}**"
    )
    return year, month


def page_bills():
    banner("Monthly Bills", "Rent + water, electricity (by unit), dustbin — every month")

    tenants = db.get_tenants()
    if not tenants:
        st.warning("Add floors and tenants first.")
        return

    year, month = month_selector("bills")
    st.divider()

    tenant_map = {f"{t['name']}": t for t in tenants}
    picked = st.selectbox("Select tenant to enter / edit this month's bill", list(tenant_map.keys()))
    tenant = tenant_map[picked]

    existing = db.get_bill(tenant["id"], year, month)

    with st.form("bill_form"):
        st.markdown(f"**Bill for {tenant['name']} — {cal.english_month_label(year, month)}**")
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

        st.markdown("**Water**")
        w1, w2 = st.columns(2)
        water_units = w1.number_input(
            "Water units used", min_value=0.0, step=1.0,
            value=float(existing["water_units"]) if existing else 0.0,
        )
        water_rate = w2.number_input(
            "Rate per water unit (Rs.)", min_value=0.0, step=1.0,
            value=float(existing["water_rate"]) if existing else 0.0,
        )

        st.markdown("**Electricity**")
        e1, e2 = st.columns(2)
        elec_units = e1.number_input(
            "Electricity units used", min_value=0.0, step=1.0,
            value=float(existing["electricity_units"]) if existing else 0.0,
        )
        elec_rate = e2.number_input(
            "Rate per electricity unit (Rs.)", min_value=0.0, step=1.0,
            value=float(existing["electricity_rate"]) if existing else 0.0,
        )

        other_desc = st.text_input(
            "Other charges description",
            value=existing["other_desc"] if existing and existing["other_desc"] else "",
        )
        paid = st.checkbox("Marked as paid", value=bool(existing["paid"]) if existing else False)

        preview_total = (
            rent + water_units * water_rate + elec_units * elec_rate + dustbin + other
        )
        st.info(f"Estimated total: **{money(preview_total)}**")

        if st.form_submit_button("Save bill", type="primary"):
            db.upsert_bill({
                "tenant_id": tenant["id"], "year_ad": year, "month_ad": month,
                "rent_amount": rent, "water_units": water_units, "water_rate": water_rate,
                "electricity_units": elec_units, "electricity_rate": elec_rate,
                "dustbin_amount": dustbin, "other_amount": other,
                "other_desc": other_desc, "paid": paid,
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
    st.subheader(f"All bills · {cal.english_month_label(year, month)}")
    st.caption(f"Nepali: {cal.nepali_month_label_for(year, month)}")

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
            "Water": (b["water_units"] or 0) * (b["water_rate"] or 0),
            "Electricity": (b["electricity_units"] or 0) * (b["electricity_rate"] or 0),
            "Dustbin": b["dustbin_amount"],
            "Other": b["other_amount"],
            "Total": total,
            "Status": "Paid" if b["paid"] else "Due",
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
                file_name=f"receipt_{b['tenant_name'].replace(' ', '_')}_{year}_{month:02d}.pdf",
                mime="application/pdf",
                key=f"rcpt_{b['id']}",
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Yearly income summary
# ---------------------------------------------------------------------------
def page_year_summary():
    banner("Yearly Summary", "Total income collected and due across the whole year")

    tenants = db.get_tenants()
    if not tenants:
        st.warning("Add floors and tenants first.")
        return

    today = cal.today_ad()
    years = list(range(today.year - 3, today.year + 2))
    year = st.selectbox("Year (AD)", years, index=years.index(today.year), key="ys_year")
    st.caption(
        f"🗓️ Nepali span: **{cal.nepali_month_label_for(year, 1)}** … "
        f"**{cal.nepali_month_label_for(year, 12)}**"
    )
    st.divider()

    bills = db.get_bills_for_year(year)

    monthly_rows = []
    tot_billed = tot_collected = tot_due = 0.0
    tot_count = 0
    for m in range(1, 13):
        mbills = [b for b in bills if b["month_ad"] == m]
        billed = sum(db.bill_total(b) for b in mbills)
        collected = sum(db.bill_total(b) for b in mbills if b["paid"])
        due = billed - collected
        tot_billed += billed
        tot_collected += collected
        tot_due += due
        tot_count += len(mbills)
        monthly_rows.append({
            "month": m,
            "eng": cal.english_month_label(year, m),
            "nep": cal.nepali_month_label_for(year, m),
            "billed": billed,
            "collected": collected,
            "due": due,
            "count": len(mbills),
        })

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, money(tot_billed), "Total billed"),
        (c2, money(tot_collected), "Total collected"),
        (c3, money(tot_due), "Total due"),
        (c4, tot_count, "Bills in the year"),
    ]:
        col.markdown(
            f"<div class='gs-metric'><div class='v'>{val}</div><div class='l'>{label}</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    table = [{
        "Month": r["eng"],
        "Nepali": r["nep"],
        "Bills": r["count"],
        "Billed": r["billed"],
        "Collected": r["collected"],
        "Due": r["due"],
    } for r in monthly_rows]
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.bar_chart(
        {"Collected": [r["collected"] for r in monthly_rows],
         "Due": [r["due"] for r in monthly_rows]},
    )

    totals = {"billed": tot_billed, "collected": tot_collected,
              "due": tot_due, "count": tot_count}
    pdf_bytes = pdf_report.generate_year_summary(year, monthly_rows, totals)
    st.download_button(
        "⬇️ Download yearly summary as PDF",
        data=pdf_bytes,
        file_name=f"yearly_summary_{year}.pdf",
        mime="application/pdf",
        type="primary",
    )


# ---------------------------------------------------------------------------
# Calendar view
# ---------------------------------------------------------------------------
def page_calendar():
    banner("Calendar", "See any month in both English (AD) and Nepali (BS)")

    year, month = month_selector("calview")
    st.divider()

    import calendar as pycal
    cal_matrix = pycal.monthcalendar(year, month)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    st.markdown(f"### {cal.english_month_label(year, month)}")
    st.caption(f"Nepali: {cal.nepali_month_label_for(year, month)}")

    header = st.columns(7)
    for i, wd in enumerate(weekdays):
        header[i].markdown(f"**{wd}**")

    today = cal.today_ad()
    for week in cal_matrix:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write(" ")
                continue
            ad = datetime.date(year, month, day)
            bs = cal.ad_to_bs(ad)
            is_today = ad == today
            box = (
                f"<div class='gs-card' style='padding:.5rem .6rem;"
                f"{'border:2px solid #0f766e;' if is_today else ''}'>"
                f"<div style='font-size:1.1rem;font-weight:700;color:#1c2b2a;'>{day}</div>"
                f"<div style='font-size:.72rem;color:#0f766e;'>{cal.NEPALI_MONTHS[bs.month-1][:3]} {bs.day}</div>"
                f"</div>"
            )
            cols[i].markdown(box, unsafe_allow_html=True)


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
