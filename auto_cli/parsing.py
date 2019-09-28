import argparse
import inspect
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union

from .types import Command
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

    def parse_args(self, args=None, namespace=None):  # type: ignore # match signature
        raise RuntimeError("Please call `parse` instead.")

    def add_param_transformer(self, param_name: str, transform: Callable) -> None:
        self.post_processing[param_name] = transform


def create_parser(command: Command) -> ArgumentParser:
    """Create a parser for the given command"""
    function = command.function
    function_doc = command.parse_function_doc()
    parameters = _get_params(function)

    parser = ArgumentParser(description=f"{command.name}: {function_doc.description}")
    param_types = command.parameter_types or {}
    short_names = command.short_names or {}
    for param_name, parameter in parameters.items():
        param_docs = function_doc.param_docs.get(param_name)
        short_name = short_names.get(param_name)
        try:
            annotation = _get_annotation(parameter, param_name, param_types)
            _add_arg_for_param(
                parser, parameter, param_name, annotation, param_docs, short_name
            )
        except ParameterException as e:
            _print_and_quit(
                f"Error processing parameter '{param_name}' of '{command.name}' "
                f"({function})': {e.args[0]}."
            )

    return parser


class ParameterException(Exception):
    pass


def _get_params(function: Callable) -> Dict[str, inspect.Parameter]:
    signature = inspect.signature(function)
    parameters = dict(signature.parameters)

    argspec = inspect.getfullargspec(function)
    # Remove *args and **kwargs because we don't support them
    if argspec.varargs is not None:
        del parameters[argspec.varargs]
    if argspec.varkw is not None:
        del parameters[argspec.varkw]
    return parameters


def _get_annotation(
    parameter: inspect.Parameter, param_name: str, param_types: Dict[str, Callable]
) -> Callable:
    annotation = param_types.get(param_name, parameter.annotation)
    if annotation == inspect.Parameter.empty:
        if _has_default(parameter):
            # Deduce the type from the default value
            annotation = type(parameter.default)
        else:
            raise ParameterException(
                "Parameter is does not have an annotation or default value"
            )

    return annotation


def _add_arg_for_param(
    parser: ArgumentParser,
    parameter: inspect.Parameter,
    param_name: str,
    annotation: Callable,
    param_docs: Optional[str],
    short_name: Optional[str],
) -> None:
    kwargs = {
        "required": not _has_default(parameter),
        "default": parameter.default if _has_default(parameter) else None,
        # The params above might be overwritten by the function below
        **_get_type_params(annotation, param_name),
    }

    names = [f"--{param_name}"]
    if short_name:
        names.append(short_name)
    parser.add_argument(*names, help=param_docs, **kwargs)
    if _is_typing_type(parameter.annotation, Tuple):
        parser.add_param_transformer(param_name, tuple)


def _has_default(parameter: inspect.Parameter) -> bool:
    """Check if parameter has a default value"""
    return parameter.default != inspect.Parameter.empty


def _get_type_params(annotation: Any, param_name: str) -> Dict[str, Any]:
    if _is_typing_type(annotation, Union):
        args = annotation.__args__
        if len(args) == 2 and args[1] is type(None):  # Optional
            return {"required": False, **_get_type_params(args[0], param_name)}
        else:
            ParameterException(f"Unions are not supported")
    elif _is_typing_type(annotation, List):
        args = annotation.__args__
        if len(args) != 1:
            raise ParameterException(
                "List should be annotated with one element type, for instance `List[int]`"
            )
        return {"nargs": "+", "type": args[0]}
    elif _is_typing_type(annotation, Tuple):
        args = annotation.__args__
        if len(args) == 0:
            raise ParameterException(
                "Tuple should be annotated with element type, for instance Tuple[int, int]"
            )
        if len(args) == 2 and args[1] is Ellipsis:
            return {"nargs": "+", "type": args[0]}
        if len(set(args)) != 1:
            raise ParameterException(
                "auto_cli only supports Tuples where each element is of the same type"
            )
        return {"nargs": len(args), "type": args[0]}
    elif annotation is bool:
        # Bools are implicitly False by default
        return {"action": "store_true", "default": False, "required": False}

    return {"type": annotation}


def _is_typing_type(annotation: Any, type_: Any) -> bool:
    origin = getattr(annotation, "__origin__", None)
    if origin is None:
        return False
    return origin is type_
