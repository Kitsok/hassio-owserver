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


def test_local_template_renderer_does_not_start_compose(monkeypatch, tmp_path):
    request = Mock()
    binary = tmp_path / "tempio"
    render = Mock(return_value="rendered locally")
    monkeypatch.setattr(conftest, "_render_with_binary", render)
    renderer = conftest.render_template.__wrapped__(binary, request)
    assert renderer({"devices": []}) == "rendered locally"
    render.assert_called_once_with(binary, {"devices": []})
    request.getfixturevalue.assert_not_called()


def test_container_template_renderer_requests_compose(monkeypatch):
    request = Mock()
    render = Mock(return_value="rendered in container")
    monkeypatch.setattr(conftest, "_render_with_container", render)
    renderer = conftest.render_template.__wrapped__(None, request)
    request.getfixturevalue.assert_called_once_with("compose_project")
    assert renderer({"devices": []}) == "rendered in container"
    render.assert_called_once_with({"devices": []})
