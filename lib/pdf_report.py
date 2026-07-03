"""
PDF generation for bill receipts and yearly income summaries using fpdf2.
All amounts are shown in Rs. Both English (AD) and Nepali (BS) dates are printed.
"""

from fpdf import FPDF

from lib import nepali_cal as cal

TEAL = (15, 118, 110)
DARK = (28, 43, 42)
GREY = (91, 113, 109)
LIGHT = (238, 253, 251)


def _money(x):
    return f"Rs. {x:,.0f}"


class _PDF(FPDF):
    title_line = "Ghar Saathi"
    subtitle_line = "House Owner Manager"

    def header(self):
        self.set_fill_color(*TEAL)
        self.rect(0, 0, self.w, 26, style="F")
        self.set_y(7)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, self.title_line, ln=1, align="L")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, self.subtitle_line, ln=1, align="L")
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 10, f"Generated on {cal.dual_today_label()[0]}  ·  Page {self.page_no()}", align="C")


def _kv_row(pdf, label, value, bold_value=False):
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    pdf.cell(60, 7, label, border=0)
    pdf.set_font("Helvetica", "B" if bold_value else "", 10)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, value, border=0, ln=1)


def generate_bill_receipt(bill, tenant, floor_name, bill_total):
    """Return PDF bytes for a single tenant's monthly bill receipt."""
    year, month = bill["year_ad"], bill["month_ad"]
    eng = cal.english_month_label(year, month)
    nep = cal.nepali_month_label_for(year, month)

    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 9, "Rent & Utility Receipt", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 6, f"Billing month:  {eng}   (Nepali: {nep})", ln=1)
    pdf.ln(3)

    # Tenant / floor block
    pdf.set_draw_color(*TEAL)
    pdf.set_line_width(0.3)
    _kv_row(pdf, "Tenant", tenant["name"] or "-", bold_value=True)
    _kv_row(pdf, "Floor / Unit", floor_name or "-")
    if tenant.get("phone"):
        _kv_row(pdf, "Phone", tenant["phone"])
    if tenant.get("id_type") and tenant.get("id_number"):
        _kv_row(pdf, tenant["id_type"], tenant["id_number"])
    pdf.ln(4)

    # Charges table
    water = (bill["water_units"] or 0) * (bill["water_rate"] or 0)
    elec = (bill["electricity_units"] or 0) * (bill["electricity_rate"] or 0)

    rows = [
        ("Rent", "", _money(bill["rent_amount"] or 0)),
        ("Water",
         f"{bill['water_units'] or 0:g} units x {_money(bill['water_rate'] or 0)}",
         _money(water)),
        ("Electricity",
         f"{bill['electricity_units'] or 0:g} units x {_money(bill['electricity_rate'] or 0)}",
         _money(elec)),
        ("Dustbin / waste", "", _money(bill["dustbin_amount"] or 0)),
        ("Other" + (f" ({bill['other_desc']})" if bill.get("other_desc") else ""), "",
         _money(bill["other_amount"] or 0)),
    ]

    # Table header
    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(70, 9, "  Charge", border=0, fill=True)
    pdf.cell(70, 9, "Detail", border=0, fill=True)
    pdf.cell(0, 9, "Amount  ", border=0, fill=True, ln=1, align="R")

    pdf.set_text_color(*DARK)
    fill = False
    for label, detail, amount in rows:
        pdf.set_fill_color(*LIGHT)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(70, 8, f"  {label}", border=0, fill=fill)
        pdf.set_text_color(*GREY)
        pdf.cell(70, 8, detail, border=0, fill=fill)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 8, f"{amount}  ", border=0, fill=fill, ln=1, align="R")
        fill = not fill

    # Total
    pdf.ln(2)
    pdf.set_fill_color(*DARK)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(140, 11, "  TOTAL", border=0, fill=True)
    pdf.cell(0, 11, f"{_money(bill_total)}  ", border=0, fill=True, ln=1, align="R")

    pdf.ln(6)
    status = "PAID" if bill["paid"] else "DUE"
    if bill["paid"]:
        pdf.set_text_color(*TEAL)
    else:
        pdf.set_text_color(190, 60, 40)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Status: {status}", ln=1)

    return bytes(pdf.output())


def generate_year_summary(year, monthly_rows, totals):
    """
    Return PDF bytes for a yearly income summary.
    monthly_rows: list of dicts with keys month, eng, nep, billed, collected, due, count.
    totals: dict with billed, collected, due, count.
    """
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 9, f"Yearly Income Summary - {year} AD", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    first_nep = cal.nepali_month_label_for(year, 1)
    last_nep = cal.nepali_month_label_for(year, 12)
    pdf.cell(0, 6, f"Nepali span: {first_nep}  ...  {last_nep}", ln=1)
    pdf.ln(4)

    # Header
    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(58, 9, "  Month", fill=True)
    pdf.cell(24, 9, "Bills", fill=True, align="C")
    pdf.cell(34, 9, "Billed", fill=True, align="R")
    pdf.cell(34, 9, "Collected", fill=True, align="R")
    pdf.cell(0, 9, "Due  ", fill=True, align="R", ln=1)

    pdf.set_text_color(*DARK)
    fill = False
    for r in monthly_rows:
        pdf.set_fill_color(*LIGHT)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(58, 8, f"  {r['eng']}", fill=fill)
        pdf.cell(24, 8, str(r["count"]), fill=fill, align="C")
        pdf.cell(34, 8, _money(r["billed"]), fill=fill, align="R")
        pdf.cell(34, 8, _money(r["collected"]), fill=fill, align="R")
        pdf.cell(0, 8, f"{_money(r['due'])}  ", fill=fill, align="R", ln=1)
        fill = not fill

    # Totals row
    pdf.ln(2)
    pdf.set_fill_color(*DARK)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(58, 10, "  TOTAL")
    pdf.cell(24, 10, str(totals["count"]), fill=True, align="C")
    pdf.cell(34, 10, _money(totals["billed"]), fill=True, align="R")
    pdf.cell(34, 10, _money(totals["collected"]), fill=True, align="R")
    pdf.cell(0, 10, f"{_money(totals['due'])}  ", fill=True, align="R", ln=1)

    return bytes(pdf.output())
