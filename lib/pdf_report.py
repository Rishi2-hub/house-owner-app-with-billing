"""
PDF generation for bill receipts and yearly income summaries.
Supports both English (AD) and Nepali (BS) dates.
"""

from fpdf import FPDF
from lib import nepali_cal as cal

TEAL = (15, 118, 110)
DARK = (28, 43, 42)
GREY = (91, 113, 109)
LIGHT = (238, 253, 251)


def _money(value):
    return f"Rs. {value:,.0f}"


class _PDF(FPDF):

    title_line = "Ghar Saathi"
    subtitle_line = "House Owner Manager"

    def header(self):
        self.set_fill_color(*TEAL)
        self.rect(0, 0, self.w, 26, style="F")

        self.set_y(7)

        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, self.title_line, ln=True)

        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, self.subtitle_line, ln=True)

        self.ln(6)

    def footer(self):

        self.set_y(-15)

        self.set_font("Helvetica", "I", 8)

        self.set_text_color(*GREY)

        eng_date, nep_date = cal.dual_today_label()

        self.cell(
            0,
            10,
            f"Generated on {nep_date} ({eng_date})   -   Page {self.page_no()}",
            align="C",
        )


def _kv_row(pdf, label, value, bold=False):

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    pdf.cell(60, 7, label)

    pdf.set_font("Helvetica", "B" if bold else "", 10)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, str(value), ln=True)

def generate_bill_receipt(bill, tenant, floor_name, bill_total):
    """
    Generate a PDF receipt for a monthly bill.
    Shows both English (AD) and Nepali (BS) billing months.
    """

    year = bill["year_ad"]
    month = bill["month_ad"]

    eng_month = cal.english_month_label(year, month)
    nep_month = cal.nepali_month_label_for(year, month)

    pdf = _PDF()
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_page()

    # ----------------------------
    # Title
    # ----------------------------
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 10, "Monthly Rent Receipt", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)

    pdf.cell(
        0,
        6,
        f"Billing Month : {nep_month}",
        ln=True,
    )

    pdf.cell(
        0,
        6,
        f"English Month : {eng_month}",
        ln=True,
    )

    pdf.ln(4)

    # ----------------------------
    # Tenant Details
    # ----------------------------

    _kv_row(pdf, "Tenant Name", tenant["name"], True)
    _kv_row(pdf, "Floor", floor_name)

    if tenant.get("phone"):
        _kv_row(pdf, "Phone", tenant["phone"])

    if tenant.get("email"):
        _kv_row(pdf, "Email", tenant["email"])

    if tenant.get("id_type"):
        _kv_row(
            pdf,
            tenant["id_type"],
            tenant.get("id_number", ""),
        )

    if tenant.get("move_in_date"):
        _kv_row(
            pdf,
            "Move In Date",
            tenant["move_in_date"],
        )

    pdf.ln(5)

    # ----------------------------
    # Charges Table Header
    # ----------------------------

    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(255, 255, 255)

    pdf.set_font("Helvetica", "B", 10)

    pdf.cell(70, 8, "Charge", 1, 0, "L", True)
    pdf.cell(60, 8, "Details", 1, 0, "L", True)
    pdf.cell(50, 8, "Amount", 1, 1, "R", True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK)

    water_total = (
        (bill.get("water_units") or 0)
        * (bill.get("water_rate") or 0)
    )

    elec_total = (
        (bill.get("electricity_units") or 0)
        * (bill.get("electricity_rate") or 0)
    )

    rows = [
        (
            "Monthly Rent",
            "",
            _money(bill.get("rent_amount", 0)),
        ),
        (
            "Water",
            f'{bill.get("water_units",0)} x {_money(bill.get("water_rate",0))}',
            _money(water_total),
        ),
        (
            "Electricity",
            f'{bill.get("electricity_units",0)} x {_money(bill.get("electricity_rate",0))}',
            _money(elec_total),
        ),
        (
            "Dustbin",
            "",
            _money(bill.get("dustbin_amount",0)),
        ),
        (
            "Other",
            bill.get("other_desc",""),
            _money(bill.get("other_amount",0)),
        ),
    ]

    fill = False

    for title, detail, amount in rows:

        if fill:
            pdf.set_fill_color(*LIGHT)
        else:
            pdf.set_fill_color(255,255,255)

        pdf.cell(70,8,title,1,0,"L",fill)
        pdf.cell(60,8,str(detail),1,0,"L",fill)
        pdf.cell(50,8,amount,1,1,"R",fill)

        fill = not fill

    # ----------------------------
    # Grand Total
    # ----------------------------

    pdf.set_fill_color(*DARK)
    pdf.set_text_color(255,255,255)

    pdf.set_font("Helvetica","B",11)

    pdf.cell(130,10,"TOTAL",1,0,"L",True)
    pdf.cell(50,10,_money(bill_total),1,1,"R",True)

    pdf.ln(5)

    pdf.set_font("Helvetica","B",12)

    if bill["paid"]:
        pdf.set_text_color(0,140,70)
        pdf.cell(0,8,"STATUS : PAID",ln=True)
    else:
        pdf.set_text_color(200,40,40)
        pdf.cell(0,8,"STATUS : UNPAID",ln=True)

    pdf.ln(8)

    eng_today, nep_today = cal.dual_today_label()

    pdf.set_font("Helvetica","",9)
    pdf.set_text_color(*GREY)

    pdf.cell(0,6,f"Generated on: {nep_today}",ln=True)
    pdf.cell(0,6,f"English Date: {eng_today}",ln=True)

    return bytes(pdf.output())

def generate_year_summary(year, monthly_rows, totals):
    """
    Generate yearly income summary PDF.

    monthly_rows:
        [
            {
                "month":1,
                "eng":"January 2026",
                "nep":"Baishakh 2083",
                "count":5,
                "billed":50000,
                "collected":47000,
                "due":3000
            }
        ]
    """

    pdf = _PDF()
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_page()

    # ----------------------------
    # Title
    # ----------------------------

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*DARK)

    pdf.cell(
        0,
        10,
        f"Yearly Income Summary ({year} AD)",
        ln=True,
    )

    first_bs = cal.nepali_month_label_for(year, 1)
    last_bs = cal.nepali_month_label_for(year, 12)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)

    pdf.cell(
        0,
        6,
        f"Nepali Period : {first_bs}  -  {last_bs}",
        ln=True,
    )

    pdf.ln(5)

    # ----------------------------
    # Table Header
    # ----------------------------

    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",9)

    pdf.cell(50,8,"English",1,0,"L",True)
    pdf.cell(45,8,"Nepali",1,0,"L",True)
    pdf.cell(18,8,"Bills",1,0,"C",True)
    pdf.cell(30,8,"Billed",1,0,"R",True)
    pdf.cell(30,8,"Paid",1,0,"R",True)
    pdf.cell(0,8,"Due",1,1,"R",True)

    pdf.set_font("Helvetica","",9)
    pdf.set_text_color(*DARK)

    fill = False

    for row in monthly_rows:

        if fill:
            pdf.set_fill_color(*LIGHT)
        else:
            pdf.set_fill_color(255,255,255)

        pdf.cell(
            50,
            8,
            row["eng"],
            1,
            0,
            "L",
            fill,
        )

        pdf.cell(
            45,
            8,
            row["nep"],
            1,
            0,
            "L",
            fill,
        )

        pdf.cell(
            18,
            8,
            str(row["count"]),
            1,
            0,
            "C",
            fill,
        )

        pdf.cell(
            30,
            8,
            _money(row["billed"]),
            1,
            0,
            "R",
            fill,
        )

        pdf.cell(
            30,
            8,
            _money(row["collected"]),
            1,
            0,
            "R",
            fill,
        )

        pdf.cell(
            0,
            8,
            _money(row["due"]),
            1,
            1,
            "R",
            fill,
        )

        fill = not fill

    # ----------------------------
    # Totals
    # ----------------------------

    pdf.ln(4)

    pdf.set_fill_color(*DARK)
    pdf.set_text_color(255,255,255)

    pdf.set_font("Helvetica","B",10)

    pdf.cell(95,10,"YEAR TOTAL",1,0,"L",True)

    pdf.cell(
        18,
        10,
        str(totals["count"]),
        1,
        0,
        "C",
        True,
    )

    pdf.cell(
        30,
        10,
        _money(totals["billed"]),
        1,
        0,
        "R",
        True,
    )

    pdf.cell(
        30,
        10,
        _money(totals["collected"]),
        1,
        0,
        "R",
        True,
    )

    pdf.cell(
        0,
        10,
        _money(totals["due"]),
        1,
        1,
        "R",
        True,
    )

    pdf.ln(8)

    eng_today, nep_today = cal.dual_today_label()

    pdf.set_font("Helvetica","",9)
    pdf.set_text_color(*GREY)

    pdf.cell(
        0,
        6,
        f"Generated: {nep_today}",
        ln=True,
    )

    pdf.cell(
        0,
        6,
        f"English Date: {eng_today}",
        ln=True,
    )

    return bytes(pdf.output())