from datetime import date, datetime, timedelta

import pytest

from bookings import BookingBook

DAY = datetime(2026, 11, 2)


def at(hour, minute=0, day=DAY):
    return day.replace(hour=hour, minute=minute)


def test_refund_tiers():
    start = at(12)
    cases = [
        (start - timedelta(hours=30), 100),
        (start - timedelta(hours=24), 100),
        (start - timedelta(hours=23, minutes=59), 50),
        (start - timedelta(hours=2), 50),
        (start - timedelta(hours=1, minutes=59), 0),
        (start + timedelta(minutes=5), 0),
    ]
    for now, refund in cases:
        book = BookingBook()
        booking = book.book("Asha", "Haircut", start, 45)
        assert book.cancel(booking.id, now) == refund


def test_cancel_frees_the_slot():
    book = BookingBook()
    booking = book.book("Asha", "Haircut", at(12), 45)
    book.cancel(booking.id, at(9))
    with pytest.raises(KeyError):
        book.get(booking.id)
    book.book("Ravi", "Shave", at(12), 30)


def test_unknown_id():
    with pytest.raises(KeyError):
        BookingBook().cancel(99, at(9))
