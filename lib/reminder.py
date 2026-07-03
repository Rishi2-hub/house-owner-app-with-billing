from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from lib import db

scheduler = BackgroundScheduler()

def check_rent_due():
    today = datetime.now()

    tenants = db.get_tenants()
    bills = db.get_bills_for_month(today.year, today.month)

    unpaid = []

    for t in tenants:
        bill = next((b for b in bills if b["tenant_id"] == t["id"]), None)

        if bill and not bill.get("paid", False):
            unpaid.append(t)

    if unpaid:
        print(f"⚠️ {len(unpaid)} unpaid rent found")
        for t in unpaid:
            print("Send reminder to:", t["name"], t.get("phone"))

def start_reminder():
    # prevent duplicate jobs
    if not scheduler.running:
        scheduler.add_job(check_rent_due, "interval", hours=6)
        scheduler.start()