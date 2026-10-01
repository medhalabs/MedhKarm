from datetime import date, datetime, timedelta

import pytest

from bookings import BookingBook

DAY = datetime(2026, 11, 2)


def at(hour, minute=0, day=DAY):
    return day.replace(hour=hour, minute=minute)


NEXT = DAY + timedelta(days=1)
LATER = DAY + timedelta(days=3)


def test_window_and_order():
    book = BookingBook()
    book.book("Late", "Cut", at(15, 0, NEXT), 30)  # 24h after now: included
    book.book("Soon", "Cut", at(11), 30)  # included
    book.book("Past", "Cut", at(9, 30), 30)  # before now: excluded
    book.book("Far", "Cut", at(16, 0, NEXT), 30)  # beyond 24h: excluded
    book.book("Away", "Cut", at(10, 0, LATER), 30)  # excluded
    due = book.reminders_due(at(15))
    assert [b.customer for b in due] == ["Late"]
    due = book.reminders_due(at(10))
    assert [b.customer for b in due] == ["Soon"]


def test_starting_exactly_now_is_excluded():
    book = BookingBook()
    book.book("Now", "Cut", at(10), 30)
    assert book.reminders_due(at(10)) == []


def test_sorted_across_days():
    book = BookingBook()
    book.book("B", "Cut", at(10, 0, NEXT), 30)
    book.book("A", "Cut", at(17), 30)
    assert [b.customer for b in book.reminders_due(at(12))] == ["A", "B"]
