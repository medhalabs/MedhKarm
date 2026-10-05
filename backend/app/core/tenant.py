"""Whose work is running right now. Background jobs and API calls set it once; deep code (an
agent's model call) reads it without every function passing the company along."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

current_company: ContextVar[str | None] = ContextVar("current_company", default=None)


@contextmanager
def company_scope(company_id: str | None) -> Iterator[None]:
    """Everything inside (and tasks started inside) runs as this company."""
    token = current_company.set(company_id)
    try:
        yield
    finally:
        current_company.reset(token)
