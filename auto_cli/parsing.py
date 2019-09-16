import argparse
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .utils import _print_and_quit


class ArgumentParser(argparse.ArgumentParser):
    """
    This class implements some additional functionality on top of
    Python's standard argparse.ArgumentParser.
    It returns the parsed parameters as a dictionary and
    has optional postprocessing of parameters.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.post_processing: Dict[str, Callable] = {}

    def parse(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        args_as_dict = vars(super().parse_args(args))
        for param_name, transform_func in self.post_processing.items():
            args_as_dict[param_name] = transform_func(args_as_dict[param_name])
        return args_as_dict

    def add_param_transformer(self, param_name: str, transform: Callable) -> None:
        self.post_processing[param_name] = transform


def create_parser(function: Callable, command_name: str) -> ArgumentParser:
    """Create a parser for the given function"""
    parser = ArgumentParser(description=f"{command_name}: {function.__doc__}")
    signature = inspect.signature(function)
    parameters = dict(signature.parameters)
    argspec = inspect.getfullargspec(function)

    if argspec.varargs is not None:
        del parameters[argspec.varargs]
    if argspec.varkw is not None:
        del parameters[argspec.varkw]

    for param_name, parameter in parameters.items():
        kwargs = {
            "required": not _has_default(parameter),
            "default": parameter.default if _has_default(parameter) else None,
            # The params above might be overwritten by the function below
            **_get_type_params(parameter.annotation, param_name, function),
        }

        parser.add_argument(f"--{param_name}", **kwargs)
        if kwargs.get("nargs", "+") != "+":  # is_tuple: TODO(joris): refactor
            parser.add_param_transformer(param_name, tuple)
        # TODO(joris): parse documentation of param for help

    return parser


def _has_default(parameter: inspect.Parameter) -> bool:
    """Check if parameter has a default value"""
    return parameter.default != inspect.Parameter.empty


def _get_type_params(
    annotation: Any, param_name: str, function: Callable
) -> Dict[str, Any]:
    def _fail(message: str) -> None:
        _print_and_quit(
            f"Error processing paramter '{param_name}' "
            f"with type {annotation} of '{function}': {message}"
        )

    if hasattr(annotation, "__origin__"):
        origin = annotation.__origin__
        if origin is Union:
            args = annotation.__args__
            if len(args) == 2 and args[1] is type(None):  # Optional
                return {
                    "required": False,
                    **_get_type_params(args[0], param_name, function),
                }
            else:
                _fail(f"Unions are not supported")
        elif origin is List:
            args = annotation.__args__
            if len(args) == 0:
                _fail(
                    "List should be annotated with element type, for instance List[int]"
                )
            return {"nargs": "+", "type": args[0]}
        elif origin is Tuple:
            args = annotation.__args__
            if len(args) == 0:
                _fail(
                    "Tuple should be annotated with element type, for instance Tuple[int, int]"
                )
            if len(set(args)) != 1:
                _fail(
                    "auto_cli only supports Tuples where each element is the same type"
                )

            return {"nargs": len(args), "type": args[0]}

    if annotation is bool:
        # Bools are implicitly False by default
        return {"action": "store_true", "default": False, "required": False}

    return {"type": annotation}
