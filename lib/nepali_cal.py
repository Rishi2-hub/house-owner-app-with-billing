"""
Helpers for converting between English (AD) and Nepali (BS) dates.
"""

import datetime
import calendar
import nepali_datetime as nd


ENGLISH_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


NEPALI_MONTHS = [
    "Baishakh",
    "Jestha",
    "Ashadh",
    "Shrawan",
    "Bhadra",
    "Ashwin",
    "Kartik",
    "Mangsir",
    "Poush",
    "Magh",
    "Falgun",
    "Chaitra",
]

def today_ad():
    return datetime.date.today()


def ad_to_bs(ad_date):
    return nd.date.from_datetime_date(ad_date)


def bs_to_ad(year, month, day=1):
    return nd.date(year, month, day).to_datetime_date()


def english_month_label(year, month):
    return f"{ENGLISH_MONTHS[month-1]} {year}"


def nepali_month_label(year, month):
    return f"{NEPALI_MONTHS[month-1]} {year} BS"

def nepali_month_label_for(year_ad, month_ad):
    """
    Converts an English month into its corresponding Nepali month.
    """

    ad = datetime.date(year_ad, month_ad, 1)

    bs = ad_to_bs(ad)

    return nepali_month_label(bs.year, bs.month)

def format_bs_date(ad_date):

    bs = ad_to_bs(ad_date)

    return f"{bs.day} {NEPALI_MONTHS[bs.month-1]} {bs.year} BS"


def dual_today_label():

    today = today_ad()

    return (
        today.strftime("%d %B %Y"),
        format_bs_date(today),
    )

def bs_month_to_ad(bs_year, bs_month):
    """
    Returns first English date of a Nepali month.
    """

    return bs_to_ad(bs_year, bs_month, 1)


def bs_month_last_day(bs_year, bs_month):

    if bs_month == 12:

        next_month = bs_to_ad(bs_year + 1, 1, 1)

    else:

        next_month = bs_to_ad(bs_year, bs_month + 1, 1)

    return next_month - datetime.timedelta(days=1)


def ad_month_from_bs(bs_year, bs_month):
    """
    Convert Nepali month into English year/month.
    """

    ad = bs_month_to_ad(bs_year, bs_month)

    return ad.year, ad.month


def current_bs():

    return ad_to_bs(today_ad())


def current_bs_year():

    return current_bs().year


def current_bs_month():

    return current_bs().month