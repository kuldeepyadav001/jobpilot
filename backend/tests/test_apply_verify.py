"""Tests for the portal-apply VERIFICATION behaviour.

Locks the fix for: jobs were recorded as 'applied' even when the portal actually
rejected / ignored the submission (stale cookie, not logged in, or the submit
failed). Now the portal path only reports 'applied' on a confirmed success signal.
"""
import pytest
from engine.apply import PlaywrightApplyEngine


class _FakeConfirmed:
    """Helper that records the apply-mode used and simulates page-query results."""

    def __init__(self, confirmed: bool):
        self.confirmed = confirmed
        self.query_selector_returns = []
        self.calls = []

    async def query_selector(self, selector):
        self.calls.append(selector)
        # Return a non-None object only for the success selectors we want to match.
        return "FOUND" if self.confirmed and "applied" in selector.lower() else None

    async def get_attribute(self, name):
        return None


@pytest.mark.asyncio
async def test_confirmed_applied_detects_success():
    eng = PlaywrightApplyEngine(headless=True)
    fake = _FakeConfirmed(confirmed=True)
    # The generic success selector path should return True for an applied string.
    result = await eng._confirmed_applied_page_probe(fake)
    assert result is True


@pytest.mark.asyncio
async def test_confirmed_applied_returns_false_when_no_signal():
    eng = PlaywrightApplyEngine(headless=True)
    fake = _FakeConfirmed(confirmed=False)
    result = await eng._confirmed_applied_page_probe(fake)
    assert result is False
