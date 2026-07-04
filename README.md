# 🏠 House Owner Rental Management System

A modern rental management application built with **Python**, **Streamlit**, and **SQLite** to help house owners manage tenants, monthly bills, utility charges, and financial reports—all in one place.

---

## 📌 Features

### 🏢 Floor Management

* Add, edit, and delete floors
* Upload a background image for each floor
* Organize tenants by floor

### 👨‍👩‍👧 Tenant Management

* Add, edit, and remove tenants
* Store tenant information

  * Name
  * Phone Number
  * Email
  * ID Type
  * ID Number
  * Rent Amount
  * Move-in Date
  * Notes
* Upload tenant profile photo
* Upload multiple tenant documents/photos

### 💰 Monthly Billing

Generate monthly bills including:

* House Rent
* Water Charges
* Electricity Charges
* Dustbin/Waste Charges
* Additional Charges
* Payment Status (Paid / Due)

Bills are automatically stored in the local SQLite database.

---

## 📅 Nepali Calendar Support

The application supports both:

* English (Gregorian) Calendar (AD)
* Nepali Calendar (Bikram Sambat - BS)

Users can:

* Select Nepali Year
* Select Nepali Month
* Automatically convert BS dates to AD dates
* Display both calendars throughout the application

---

## 📄 PDF Reports

Generate professional PDF reports including:

* Monthly Tenant Bill Receipt
* Yearly Income Summary

PDFs include:

* Tenant Details
* Floor Information
* Rent Details
* Utility Charges
* Total Amount
* Payment Status
* English and Nepali Dates

---

## 📊 Dashboard

Dashboard includes:

* Total Floors
* Total Tenants
* Paid Bills
* Due Bills
* Monthly Income
* Outstanding Balance

---

## 💾 Database

Database: **SQLite**

Tables:

* Floors
* Tenants
* Bills

All information is stored locally.

---

## 📁 Project Structure

```text
house-owner-app-with-billing/
│
├── app.py
├── requirements.txt
├── data/
│   ├── house.db
│   └── uploads/
│
├── lib/
│   ├── db.py
│   ├── pdf_report.py
│   ├── nepali_cal.py
│   └── ...
│
└── README.md
```

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/house-owner-app-with-billing.git
```

```bash
cd house-owner-app-with-billing
```

### Create a virtual environment (Optional)

Windows

```bash
python -m venv venv
```

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the application

```bash
streamlit run app.py
```

---

## Technologies Used

* Python
* Streamlit
* SQLite
* FPDF2
* Nepali Datetime
* Pandas
* Pillow

---

## Future Improvements

* User Authentication
* Backup & Restore Database
* Email Bill Receipts
* SMS Notifications
* Online Cloud Database
* Mobile Application
* Analytics Dashboard
* Expense Tracking
* Multiple Property Support
* Tenant Portal

---

## Screenshots

Add screenshots here after uploading your project.

Example:

* Dashboard
* Floor Management
* Tenant Management
* Monthly Billing
* Yearly Summary
* PDF Receipt

---

## Author

**Rishi Kumar Kushwaha**

Python Developer | Data Science Enthusiast | Software Developer

LinkedIn:
https://www.linkedin.com/in/rishi-kumar-kushwaha-1b89462b0/

GitHub:
https://github.com/yourusername

---

## License

This project is licensed under the MIT License.

Feel free to use, modify, and improve this project for learning or personal use.
