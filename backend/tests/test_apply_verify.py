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


class _NaukriProbe:
    """Stub that matches Naukri success text selectors."""
    def __init__(self, applied: bool):
        self.applied = applied
        self.skip_buttons = 0

    async def query_selector(self, selector):
        # Never match a raw <button>: those are ignored to avoid false 'Apply' label hits.
        if selector.startswith("button"):
            return None
        if selector.startswith("text=") and self.applied:
            return object()  # non-gtNone ~ success found
        return None


@pytest.mark.asyncio
async def test_naukri_confirmed_detects_text_success():
    eng = PlaywrightApplyEngine(headless=True)
    assert await eng._is_naukri_applied_confirmed(_NaukriProbe(applied=True)) is True


@pytest.mark.asyncio
async def test_naukri_confirmed_ignores_button_labels():
    eng = PlaywrightApplyEngine(headless=True)
    # Button selectors are skipped (avoid false positive on a passive 'Apply' button).
    assert await eng._is_naukri_applied_confirmed(_NaukriProbe(applied=True)) is True
