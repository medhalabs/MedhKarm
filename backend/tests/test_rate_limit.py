from app.shared.rate_limit import RateLimiter


def test_an_address_gets_its_attempts_then_waits_for_the_window() -> None:
    now = [0.0]
    limiter = RateLimiter(limit=2, seconds=60, clock=lambda: now[0])

    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")  # used up
    assert limiter.allow("b")  # another address is separate
    now[0] = 61.0
    assert limiter.allow("a")  # the window passed
