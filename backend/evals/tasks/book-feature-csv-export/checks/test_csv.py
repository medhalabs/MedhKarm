from datetime import date, datetime, timedelta

import pytest

from bookings import BookingBook

DAY = datetime(2026, 11, 2)


def at(hour, minute=0, day=DAY):
    return day.replace(hour=hour, minute=minute)


import csv
import io


def test_rows_sorted_with_times():
    book = BookingBook()
    book.book("Ravi", "Shave", at(15), 30)
    book.book("Asha", "Haircut", at(9, 5), 45)
    text = book.export_csv(date(2026, 11, 2))
    assert (
        text
        == "id,customer,service,start,end\n2,Asha,Haircut,09:05,09:50\n1,Ravi,Shave,15:00,15:30\n"
    )


def test_empty_day_has_header_only():
    assert BookingBook().export_csv(date(2026, 11, 2)) == "id,customer,service,start,end\n"


def test_commas_are_quoted():
    book = BookingBook()
    book.book("Rao, K.", 'Colour "gold"', at(10), 60)
    rows = list(csv.reader(io.StringIO(book.export_csv(date(2026, 11, 2)))))
    assert rows[1] == ["1", "Rao, K.", 'Colour "gold"', "10:00", "11:00"]


def test_other_days_excluded():
    book = BookingBook()
    book.book("Asha", "Haircut", at(10, 0, DAY + timedelta(days=1)), 30)
    assert book.export_csv(date(2026, 11, 2)).count("\n") == 1
