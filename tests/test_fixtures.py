"""Check test orchestration without starting containers."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import conftest


@pytest.mark.parametrize("reuse,expected", [(None, "--build"), ("1", "--no-build")])
def test_compose_build_policy(monkeypatch, tmp_path, reuse, expected):
    if reuse is None:
        monkeypatch.delenv("OWSERVER_TEST_REUSE_IMAGE", raising=False)
    else:
        monkeypatch.setenv("OWSERVER_TEST_REUSE_IMAGE", reuse)
    run = Mock(return_value=SimpleNamespace(returncode=0, stdout="base-image"))
    monkeypatch.setattr(conftest.subprocess, "run", run)
    monkeypatch.setattr(conftest.subprocess, "check_output", Mock(return_value="/usr/bin"))
    monkeypatch.setattr(conftest, "_wait_for_owhttpd", Mock())
    factory = SimpleNamespace(mktemp=lambda name: tmp_path)
    fixture = conftest.compose_project.__wrapped__(factory)
    next(fixture)
    try:
        command = run.call_args.args[0]
        assert command == [*conftest.COMPOSE_CMD, "up", "-d", expected]
    finally:
        with pytest.raises(StopIteration):
            next(fixture)
