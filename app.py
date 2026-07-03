"""
Ghar Saathi — House Owner Rental Management
Offline Streamlit app with reminders, WhatsApp, backup
"""

import os
import base64
import datetime
import streamlit as st

from lib import db
from lib import nepali_cal as cal
from lib import pdf_report

# ✅ NEW FEATURES IMPORTS
from lib.reminder import start_reminder
from lib.notify import send_whatsapp
from lib.backup import backup_db


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANNER = os.path.join(BASE_DIR, "assets", "house_bg.png")

st.set_page_config(
    page_title="Ghar Saathi — House Manager",
    page_icon="🏠",
    layout="wide",
)

db.init_db()


# -----------------------------
# START AUTO REMINDER SYSTEM
# -----------------------------
def init_services():
    start_reminder()   # runs background scheduler


# -----------------------------
# CSS
# -----------------------------
def inject_css():
    st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem;}
    .gs-banner {
        border-radius: 14px;
        padding: 2rem;
        color: white;
        margin-bottom: 1rem;
        background-size: cover;
        background-position: center;
    }
    </style>
    """, unsafe_allow_html=True)


def banner(title, subtitle):
    st.markdown(f"""
    <div class="gs-banner">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def money(x):
    return f"Rs. {x:,.0f}"


# -----------------------------
# DASHBOARD
# -----------------------------
def page_dashboard():
    banner("Dashboard", "Overview")

    st.write("🏢 Floors:", len(db.get_floors()))
    st.write("👤 Tenants:", len(db.get_tenants()))


# -----------------------------
# FLOORS
# -----------------------------
def page_floors():
    banner("Floors", "Manage floors")

    with st.form("add_floor"):
        name = st.text_input("Floor Name")
        desc = st.text_area("Description")

        if st.form_submit_button("Add Floor"):
            if name:
                db.add_floor(name, desc, None)
                st.success("Added")
                st.rerun()


# -----------------------------
# TENANTS + WHATSAPP BUTTON
# -----------------------------
def page_tenants():
    banner("Tenants", "Manage tenants")

    floors = {f["name"]: f["id"] for f in db.get_floors()}

    if not floors:
        st.warning("Add floors first")
        return

    with st.form("add_tenant"):
        floor = st.selectbox("Floor", list(floors.keys()))
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        rent = st.number_input("Rent", 0.0)

        if st.form_submit_button("Add Tenant"):
            db.add_tenant({
                "floor_id": floors[floor],
                "name": name,
                "phone": phone,
                "rent_amount": rent
            })
            st.success("Added")
            st.rerun()

    st.divider()

    tenants = db.get_tenants()

    for t in tenants:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"👤 {t['name']} — {money(t['rent_amount'])}")

        # 📩 WHATSAPP REMINDER BUTTON
        with col2:
            if st.button("📩 Send Reminder", key=f"msg_{t['id']}"):
                msg = f"""
Hello {t['name']},
Your rent of Rs.{t['rent_amount']} is due.
Please pay soon.
"""
                send_whatsapp(t["phone"], msg)
                st.success("Message sent")


# -----------------------------
# BILLS
# -----------------------------
def page_bills():
    banner("Bills", "Monthly system")
    st.info("Billing module already exists in your full version")


# -----------------------------
# BACKUP BUTTON (GOOGLE DRIVE)
# -----------------------------
def backup_section():
    st.sidebar.divider()

    if st.sidebar.button("☁️ Backup to Google Drive"):
        file_id = backup_db()
        st.sidebar.success("Backup completed")
        st.sidebar.caption(f"File ID: {file_id}")


# -----------------------------
# MAIN
# -----------------------------
def main():
    inject_css()

    # ✅ start auto reminder system
    init_services()

    # sidebar menu
    page = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Floors", "Tenants", "Bills"]
    )

    # ☁️ backup button in sidebar
    backup_section()

    if page == "Dashboard":
        page_dashboard()
    elif page == "Floors":
        page_floors()
    elif page == "Tenants":
        page_tenants()
    elif page == "Bills":
        page_bills()


if __name__ == "__main__":
    main()