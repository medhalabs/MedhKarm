"""Appointment book for a salon."""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class Booking:
    id: int
    customer: str
    service: str
    start: datetime
    end: datetime


class BookingBook:
    def __init__(self, opening_hour: int = 9, closing_hour: int = 19) -> None:
        self.opening_hour = opening_hour
        self.closing_hour = closing_hour
        self._bookings: dict[int, Booking] = {}
        self._next_id = 1

    def book(self, customer: str, service: str, start: datetime, duration_minutes: int) -> Booking:
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        end = start + timedelta(minutes=duration_minutes)
        closing = start.replace(hour=self.closing_hour, minute=0, second=0, microsecond=0)
        if start.hour < self.opening_hour or end > closing:
            raise ValueError("Outside opening hours")
        for existing in self._bookings.values():
            if start <= existing.end and existing.start <= end:
                raise ValueError("Slot already booked")
        booking = Booking(self._next_id, customer, service, start, end)
        self._bookings[booking.id] = booking
        self._next_id += 1
        return booking

    def get(self, booking_id: int) -> Booking:
        return self._bookings[booking_id]

    def bookings_on(self, day: date) -> list[Booking]:
        found = [b for b in self._bookings.values() if b.start.date() == day]
        return sorted(found, key=lambda b: b.start)

    def export_csv(self, day: date) -> str:
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["id", "customer", "service", "start", "end"])
        for b in self.bookings_on(day):
            writer.writerow(
                [b.id, b.customer, b.service, b.start.strftime("%H:%M"), b.end.strftime("%H:%M")]
            )
        return out.getvalue()
