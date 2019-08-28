from auto_cli.cli import create_parser, run_func_with_argv
import pytest


def test_create_parser_simple() -> None:
    def func_to_test(a: int, b: str) -> int:
        return a + len(b)

    parser = create_parser(func_to_test)
    args = parser.parse_args(["--a", "42", "--b", "1234"])
    assert vars(args) == {"a": 42, "b": "1234"}


def test_create_parser_defaults() -> None:
    def func_to_test(a: int, b: int = 38) -> int:
        return a + b

    parser = create_parser(func_to_test)
    args_no_default = parser.parse_args(["--a", "1", "--b", "42"])
    assert vars(args_no_default) == {"a": 1, "b": 42}

    args_with_default = parser.parse_args(["--a", "1"])
    assert vars(args_with_default) == {"a": 1, "b": 38}


@pytest.mark.xfail
def test_create_parser_list() -> None:
    assert False


@pytest.mark.xfail
def test_create_parser_tuple() -> None:
    assert False


def test_run_func_with_argv() -> None:
    def func_to_test(a: int, b: int = 38) -> int:
        return a + b

    result = run_func_with_argv(func_to_test, ["--a", "4"])
    assert result == 42
