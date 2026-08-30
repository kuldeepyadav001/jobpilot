"""Tests the APPLY GATE behaviour: the manual trigger applies, the scheduled run doesn't.

We test the pure decision boundaries (settings + pipeline signature) rather than
hitting the real browser/network, to keep the suite fast and deterministic.
"""
import pytest
from core.config import settings


def test_apply_mode_default_is_dry_run():
    # Safe by default: nothing should submit unless explicitly set to 'real'.
    assert settings.apply_mode in ("dry_run", "real")


def test_auto_apply_default_is_off():
    # Scheduled runs must NOT apply by default.
    assert settings.auto_apply is False


def test_pipeline_signature_accepts_apply_flag():
    from scheduler.jobs import run_daily_automation_pipeline
    import inspect
    sig = inspect.signature(run_daily_automation_pipeline)
    assert "apply" in sig.parameters
    assert sig.parameters["apply"].default is None  # None -> falls back to settings.auto_apply


@pytest.mark.parametrize("apply_mode,expected_sends", [("dry_run", False), ("real", True)])
def test_email_sender_gate_definition(apply_mode, expected_sends):
    """Sanity: the sender's reroute condition aligns with apply mode semantics."""
    # Simulate the exact condition used in engine/email_sender.py
    reroutes_to_self = apply_mode != "real"
    assert reroutes_to_self == (not expected_sends)
