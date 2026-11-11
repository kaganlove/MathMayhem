"""Pytest configuration and sandbox-compatible Windows event loop fixture."""

from __future__ import annotations

import asyncio
import socket
import sys


if sys.platform == "win32":
    class _LoopbackFreeProactorEventLoop(asyncio.ProactorEventLoop):
        """ProactorEventLoop subclass that replaces TCP loopback self-pipe with in-memory dummy sockets when sandboxed."""

        def _make_self_pipe(self) -> None:
            try:
                # Probe whether loopback socketpair is allowed in the current environment
                probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                probe.bind(("127.0.0.1", 0))
                probe.listen(1)
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.setblocking(False)
                try:
                    client.connect(("127.0.0.1", probe.getsockname()[1]))
                except BlockingIOError:
                    pass
                probe.settimeout(0.05)
                srv, _ = probe.accept()
                srv.close()
                client.close()
                probe.close()
                super()._make_self_pipe()
            except OSError:
                # Sandbox blocks TCP loopback; attach two unbound sockets and skip self-pipe polling
                self._ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._internal_fds += 1

        def _loop_self_reading(self, f=None) -> None:
            return

        def _write_to_self(self) -> None:
            return

    class _SandboxProactorEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
        _loop_factory = _LoopbackFreeProactorEventLoop

    asyncio.set_event_loop_policy(_SandboxProactorEventLoopPolicy())


import faulthandler
import pytest


@pytest.fixture(autouse=True)
def _per_test_watchdog_timeout():
    """Enforce a 30-second per-test watchdog timer so no test can ever hang silently."""
    faulthandler.dump_traceback_later(30, repeat=False, exit=True)
    try:
        yield
    finally:
        faulthandler.cancel_dump_traceback_later()

