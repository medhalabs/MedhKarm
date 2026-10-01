from datetime import date, datetime

import pytest

from bookings import BookingBook

DAY = datetime(2026, 11, 2)


def at(hour: int, minute: int = 0) -> datetime:
    return DAY.replace(hour=hour, minute=minute)


def test_book_and_get():
    book = BookingBook()
    booking = book.book("Asha", "Haircut", at(10), 45)
    assert book.get(booking.id).end == at(10, 45)


def test_overlap_rejected():
    book = BookingBook()
    book.book("Asha", "Haircut", at(10), 60)
    with pytest.raises(ValueError):
        book.book("Ravi", "Shave", at(10, 30), 30)


def test_outside_opening_hours_rejected():
    book = BookingBook()
    with pytest.raises(ValueError):
        book.book("Asha", "Haircut", at(8), 30)
    with pytest.raises(ValueError):
        book.book("Asha", "Haircut", at(18, 45), 30)


def test_bookings_on_day_sorted():
    book = BookingBook()
    book.book("Ravi", "Shave", at(15), 30)
    book.book("Asha", "Haircut", at(10), 45)
    assert [b.customer for b in book.bookings_on(date(2026, 11, 2))] == ["Asha", "Ravi"]
