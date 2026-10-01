from datetime import date, datetime, timedelta

import pytest

from bookings import BookingBook

DAY = datetime(2026, 11, 2)


def at(hour, minute=0, day=DAY):
    return day.replace(hour=hour, minute=minute)


def test_back_to_back_after():
    book = BookingBook()
    book.book("Asha", "Haircut", at(10), 45)
    book.book("Ravi", "Shave", at(10, 45), 30)
    assert len(book.bookings_on(date(2026, 11, 2))) == 2


def test_back_to_back_before():
    book = BookingBook()
    book.book("Asha", "Haircut", at(11), 60)
    book.book("Ravi", "Shave", at(10, 30), 30)
    assert len(book.bookings_on(date(2026, 11, 2))) == 2


@pytest.mark.parametrize(
    "hour,minute,duration", [(10, 44, 30), (10, 0, 45), (9, 30, 60), (10, 10, 10)]
)
def test_real_overlaps_still_rejected(hour, minute, duration):
    book = BookingBook()
    book.book("Asha", "Haircut", at(10), 45)
    with pytest.raises(ValueError):
        book.book("Ravi", "Shave", at(hour, minute), duration)
