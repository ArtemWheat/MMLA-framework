from __future__ import annotations

import io
from contextlib import redirect_stdout
from unittest.mock import AsyncMock, patch

from cli import main as cli_main
from core.domain.value_objects import CaseId


class DummyRuntime:
    def __init__(self, cases):
        self.registered_cases = cases
        self.case_manager = DummyCaseManager()
        self.shutdown_called = False

    async def shutdown(self) -> None:
        self.shutdown_called = True


class DummyCaseManager:
    def __init__(self):
        self.activated = []
        self.deactivated = False

    async def activate(self, case_id: CaseId) -> None:
        self.activated.append(case_id)

    async def deactivate_all(self) -> None:
        self.deactivated = True


@patch("cli.create_runtime", new_callable=AsyncMock)
def test_cli_list_command(mock_create_runtime):
    runtime = DummyRuntime([CaseId("alpha"), CaseId("beta")])
    mock_create_runtime.return_value = runtime

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = cli_main(["list"])

    output = buffer.getvalue()
    assert exit_code == 0
    assert "alpha" in output and "beta" in output
    assert runtime.shutdown_called
    mock_create_runtime.assert_awaited_once()


@patch("cli.create_runtime", new_callable=AsyncMock)
def test_cli_run_command(mock_create_runtime):
    runtime = DummyRuntime([CaseId("alpha")])
    mock_create_runtime.return_value = runtime

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = cli_main(
            [
                "run",
                "alpha",
                "--duration",
                "0",
                "--device-serial",
                "alpha=rs123",
                "--metadata",
                "alpha:location=barn",
            ]
        )

    assert exit_code == 0
    assert runtime.case_manager.activated[0] == CaseId("alpha")
    assert runtime.case_manager.deactivated
    assert runtime.shutdown_called
    await_kwargs = mock_create_runtime.await_args.kwargs
    assert await_kwargs["device_serials"] == {"alpha": "rs123"}
    assert await_kwargs["metadata"] == {"alpha": {"location": "barn"}}
