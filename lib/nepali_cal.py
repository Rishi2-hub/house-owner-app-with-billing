"""
Helpers to convert between the English (AD / Gregorian) and Nepali
(Bikram Sambat) calendars and to render friendly month labels.
"""

import datetime
import nepali_datetime as nd

ENGLISH_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Nepali (Bikram Sambat) month names in order.
NEPALI_MONTHS = [
    "Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra",
]


def ad_to_bs(ad_date):
    """Convert a datetime.date (AD) to a nepali_datetime.date (BS)."""
    return nd.date.from_datetime_date(ad_date)


def today_ad():
    return datetime.date.today()


def english_month_label(year_ad, month_ad):
    """e.g. 'July 2026'."""
    return f"{ENGLISH_MONTHS[month_ad - 1]} {year_ad}"


def nepali_month_label_for(year_ad, month_ad):
    """
    Given an English year/month, return the Nepali BS label that the 1st of
    that English month falls into, e.g. 'Ashadh/Shrawan 2083'. Because a single
    English month spans two BS months, we show the BS month of both the 1st and
    the last day when they differ.
    """
    first = datetime.date(year_ad, month_ad, 1)
    if month_ad == 12:
        last = datetime.date(year_ad, 12, 31)
    else:
        last = datetime.date(year_ad, month_ad + 1, 1) - datetime.timedelta(days=1)

    bs_first = ad_to_bs(first)
    bs_last = ad_to_bs(last)

    name_first = NEPALI_MONTHS[bs_first.month - 1]
    name_last = NEPALI_MONTHS[bs_last.month - 1]

    if bs_first.month == bs_last.month and bs_first.year == bs_last.year:
        return f"{name_first} {bs_first.year} BS"
    if bs_first.year == bs_last.year:
        return f"{name_first}/{name_last} {bs_first.year} BS"
    return f"{name_first} {bs_first.year}/{name_last} {bs_last.year} BS"


def format_bs_date(ad_date):
    """Format an AD date into a readable BS date like '18 Ashadh 2083 BS'."""
    bs = ad_to_bs(ad_date)
    return f"{bs.day} {NEPALI_MONTHS[bs.month - 1]} {bs.year} BS"


def dual_today_label():
    """Return (english, nepali) strings for today."""
    t = today_ad()
    eng = t.strftime("%d %B %Y")
    return eng, format_bs_date(t)
