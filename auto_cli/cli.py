import argparse
import inspect
from typing import Callable, List, TypeVar


def _has_default(parameter: inspect.Parameter) -> bool:
    return parameter.default != inspect.Parameter.empty


def create_parser(function: Callable) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{function.__name__}: {function.__doc__}"
    )
    signature = inspect.signature(function)

    for param_name, parameter in signature.parameters.items():
        required = not _has_default(parameter)
        default = parameter.default if _has_default(parameter) else None

        parser.add_argument(
            f"--{param_name}",
            type=parameter.annotation,
            required=required,
            default=default,
        )
        # TODO(joris): parse documentation of param for help

    return parser


ReturnType = TypeVar("ReturnType")


def run_func_with_argv(
    function: Callable[..., ReturnType], argv: List[str]
) -> ReturnType:
    parser = create_parser(function)
    args = parser.parse_args(argv)
    retval = function(**vars(args))
    return retval


def run_func_with_argv_and_print(
    function: Callable[..., ReturnType], argv: List[str]
) -> None:
    print(run_func_with_argv(function, argv))
