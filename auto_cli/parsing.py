import argparse
import inspect
import re
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
    function_doc = _parse_function_doc(function)
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
    if kwargs.get("nargs", "+") != "+":  # is_tuple: TODO(joris): refactor
        parser.add_param_transformer(param_name, tuple)


def _has_default(parameter: inspect.Parameter) -> bool:
    """Check if parameter has a default value"""
    return parameter.default != inspect.Parameter.empty


def _get_type_params(annotation: Any, param_name: str) -> Dict[str, Any]:
    if hasattr(annotation, "__origin__"):
        origin = annotation.__origin__
        if origin is Union:
            args = annotation.__args__
            if len(args) == 2 and args[1] is type(None):  # Optional
                return {"required": False, **_get_type_params(args[0], param_name)}
            else:
                ParameterException(f"Unions are not supported")
        elif origin is List:
            args = annotation.__args__
            if len(args) != 1:
                raise ParameterException(
                    "List should be annotated with one element type, for instance `List[int]`"
                )
            return {"nargs": "+", "type": args[0]}
        elif origin is Tuple:
            args = annotation.__args__
            if len(args) == 0:
                raise ParameterException(
                    "Tuple should be annotated with element type, for instance Tuple[int, int]"
                )
            if len(set(args)) != 1:
                raise ParameterException(
                    "auto_cli only supports Tuples where each element is of the same type"
                )

            return {"nargs": len(args), "type": args[0]}

    if annotation is bool:
        # Bools are implicitly False by default
        return {"action": "store_true", "default": False, "required": False}

    return {"type": annotation}


class _FunctionDoc(NamedTuple):
    description: str
    param_docs: Dict[str, str]


def _parse_function_doc(function: Callable) -> _FunctionDoc:
    """Parse function documentation which adheres to the Sphinx standard
    https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#info-field-lists
    """
    if not hasattr(function, "__doc__") or function.__doc__ is None:
        return _FunctionDoc("", {})

    doc = function.__doc__
    if not ":param" in doc:
        # Doesn't conform to our standard, so the whole __doc__ is just
        # the description of the function
        return _FunctionDoc(doc, {})

    # Now that we know doc conforms to our standard, we can extract the
    # parameter descriptions

    params_docs = {}
    for line in doc.splitlines():
        line = line.strip()
        if line.startswith(":param"):
            line = line.lstrip(":param")
            before, _, description = line.partition(":")
            param_name = before.strip().split(" ")[-1]
            params_docs[param_name] = description.strip()

    fn_description, _, _ = doc.partition(":param")
    fn_description = _normalize_whitespace(fn_description.strip())
    return _FunctionDoc(fn_description, params_docs)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)
