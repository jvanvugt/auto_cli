import importlib
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .configuration import Configuration
from .parsing import create_parser
from .types import Command
from .utils import _print_and_quit


def run_func_with_argv(command: Command, argv: List[str]) -> Any:
    parser = create_parser(command)
    args = parser.parse(argv)
    retval = command.function(**args)
    if command.return_type is not None:
        retval = command.return_type(retval)
    return retval


def run_func_with_argv_and_print(command: Command, argv: List[str]) -> None:
    result = run_func_with_argv(command, argv)
    if result is not None:
        print(result)


# In practice, this dict will be overriden by _load_app
# but it is here to keep the linters happy and for testing
REGISTERED_COMMANDS: Dict[str, Command] = {}


def register_command(
    function: Union[str, Callable[..., Any]],
    name: Optional[str] = None,
    parameter_types: Optional[Dict[str, Callable]] = None,
    return_type: Optional[Callable[[Any], Any]] = None,
    short_names: Optional[Dict[str, str]] = None,
) -> None:
    """Register ``function`` as an available command

    :param function: the function register
    :param name: Override the name of the function in the cli
                 Defaults to ``function.__name__``
    :param parameter_types: Override the type of an argument
                            Dictionary of name of the parameter to type
    :param return_type: Override the return_type of the function.
                        Will be called before printing the result to stdout.
    :param short_names: Optionally add a short version of the parameter.
                        Dictionary of name of the parameter to shorter name.
                        For instance ``{"very_long_name": "-l"}``.
    """
    python_function: Callable
    if isinstance(function, str):
        python_function = _get_function_from_str(function)
    else:
        python_function = function
    command_name = name or python_function.__name__
    command = Command(
        command_name, python_function, parameter_types, return_type, short_names
    )
    # REGISTERED_COMMANDS is magically defined by _load_app
    REGISTERED_COMMANDS[command_name] = command


def register_app(name: str, location: Optional[Path] = None) -> None:
    """Register an app with auto_cli

    :param name: Name of the app
    :param location: Parent directory of the auto_cli.py file.
                     Defaults to the current working directory.
    """
    with Configuration() as config:
        config.register_app(name, location)


def delete_app(name: str) -> str:
    """Delete the app

    :param name: Name of the app
    """
    with Configuration() as config:
        config.delete_app(name)
    return f"Deleted {name}"


def run_command(app: str, argv: List[str]) -> None:
    """Run a command in app"""
    commands = _load_app(app)
    if len(argv) == 0:
        command_help = _command_help(commands)
        _print_and_quit(
            f"No command given. Available commands:\n{command_help}", is_error=False
        )
    command_name, *argv = argv
    command = commands[command_name]
    run_func_with_argv_and_print(command, argv)


def run() -> None:
    """Main entrypoint for auto_cli, run an app and command based on sys.argv"""
    if len(sys.argv) < 2:
        _print_and_quit(
            "Did not understand command.\nUsage: ac <app> <command> [paramaters]"
        )
    app = sys.argv[1]
    run_command(app, sys.argv[2:])


def apps() -> List[str]:
    """Get all registered apps"""
    with Configuration() as config:
        return config.get_apps()


def _get_function_from_str(path: str) -> Callable:
    """Return the Python function pointed to by `path`"""
    module_name, _, function_name = path.rpartition(".")
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    return function


def _load_app(name: str) -> Dict[str, Command]:
    """Load the commands registered in auto_cli.py"""
    with Configuration() as config:
        ac_code = config.get_app_ac_content(name)

    # We want ac_code to be executed and fill a variable
    # that is local to this function with the possible commands.
    # Hence, we override the global REGISTERED_COMMANDS
    # with a dictionary that we can return from this function.
    ac_code = "\n".join(
        [
            "import auto_cli",
            "auto_cli.cli.REGISTERED_COMMANDS = REGISTERED_COMMANDS",
            ac_code,
        ]
    )

    registered_commands: Dict[str, Command] = {}
    exec(ac_code, {"REGISTERED_COMMANDS": registered_commands})
    return registered_commands


def _command_help(commands: Dict[str, Command]) -> str:
    pad_left = max(map(len, commands)) + 4
    function_docs = {
        name: command.parse_function_doc() for name, command in commands.items()
    }
    return "\n".join(
        f"{name.ljust(pad_left)}{function_docs[name].description}"
        for name, command in commands.items()
    )
