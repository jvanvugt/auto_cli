from typing import List, Tuple

import pytest

from auto_cli.parsing import create_parser
from auto_cli.types import Command


def test_create_parser_simple() -> None:
    def func_to_test(a: int, b: str) -> int:
        return a + len(b)

    parser = create_parser(Command.from_func(func_to_test))
    args = parser.parse(["--a", "42", "--b", "1234"])
    assert args == {"a": 42, "b": "1234"}


def test_create_parser_defaults() -> None:
    def func_to_test(a: int, b: int = 38) -> int:
        return a + b

    parser = create_parser(Command.from_func(func_to_test))
    args_no_default = parser.parse(["--a", "1", "--b", "42"])
    assert args_no_default == {"a": 1, "b": 42}

    args_with_default = parser.parse(["--a", "1"])
    assert args_with_default == {"a": 1, "b": 38}


def test_create_parser_bool() -> None:
    def func_to_test(a: bool) -> bool:
        return a

    parser = create_parser(Command.from_func(func_to_test))
    args_with_flag = parser.parse(["--a"])
    assert args_with_flag == {"a": True}

    args_without_flag = parser.parse([])
    assert args_without_flag == {"a": False}


def test_create_parser_list() -> None:
    def func_to_test(a: List[int]) -> int:
        return sum(a)

    parser = create_parser(Command.from_func(func_to_test))
    nums = [1, 3, 5, 7]
    args = parser.parse(["--a"] + list(map(str, nums)))

    assert args == {"a": nums}


def test_create_parser_tuple() -> None:
    def func_to_test(a: Tuple[int, int], b: bool) -> int:
        return sum(a)

    parser = create_parser(Command.from_func(func_to_test))
    nums = (42, 1337)
    args = parser.parse(["--a"] + list(map(str, nums)))

    assert args == {"a": nums, "b": False}


def test_type_from_default() -> None:
    def func_to_test(a=4) -> int:
        return a

    parser = create_parser(Command.from_func(func_to_test))
    args = parser.parse(["--a", "4"])
    assert args == {"a": 4}


def test_override_param_type() -> None:
    def func_to_test(a: int, b):
        return a + b

    command = Command("cmd_name", func_to_test, {"b": int})
    parser = create_parser(command)
    args = parser.parse(["--a", "4", "--b", "5"])
    assert args == {"a": 4, "b": 5}


def test_parse_function_doc() -> None:
    def func_to_test(a: int, b: str) -> int:
        """This is a function
        which does some interesting things

        :param int a: the number that is returned
        :param b: ignored
        """
        return a

    command = Command.from_func(func_to_test)
    docs = command.parse_function_doc()
    assert docs.description == "This is a function which does some interesting things"
    assert docs.param_docs == {"a": "the number that is returned", "b": "ignored"}


def test_create_parser_unsupported_type() -> None:
    def func_to_test(a: Tuple[int, float]) -> float:
        return sum(a)

    with pytest.raises(SystemExit):
        create_parser(Command.from_func(func_to_test))


def test_create_parser_short_opts() -> None:
    def func_to_test(long_name: int) -> int:
        return long_name

    command = Command.from_func(func_to_test)
    command = command._replace(short_names={"long_name": "-l"})
    parser = create_parser(command)
    args = parser.parse(["-l", "4"])
    assert args == {"long_name": 4}


def test_create_parser_tuple_var_length() -> None:
    def func_to_test(a: Tuple[int, ...]) -> int:
        return sum(a)

    command = Command.from_func(func_to_test)
    parser = create_parser(command)
    nums = (1, 2, 3)
    args = parser.parse(["--a"] + list(map(str, nums)))
    assert args == {"a": nums}
