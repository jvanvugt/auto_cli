from typing import Any

import pytest_mock

from auto_cli import cli


def test_run_func_with_argv() -> None:
    def func_to_test(a: int, b: int = 38) -> int:
        return a + b

    result = cli.run_func_with_argv(func_to_test, ["--a", "4"], func_to_test.__name__)
    assert result == 42


def test_register_command() -> None:
    cli.register_command("auto_cli.cli.register_app")
    assert "register_app" in cli.REGISTERED_COMMANDS


def test_run_command(mocker: pytest_mock.MockFixture) -> None:
    mocked_cmd = mocker.MagicMock()

    def register_func(_: str):
        cli.REGISTERED_COMMANDS["test_cmd"] = mocked_cmd

    mocker.patch("auto_cli.cli._load_app", register_func)
    cli.run_command("my_app", ["test_cmd"])
    mocked_cmd.assert_called_once()


def test_run(mocker: pytest_mock.MockFixture) -> None:
    mocked_run_command = mocker.patch("auto_cli.cli.run_command")
    mocker.patch("sys.argv", ["ac", "my_app", "my_cmd"])
    cli.run()

    mocked_run_command.assert_called_once()
