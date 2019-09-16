import importlib
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, TypeVar, Union

from .configuration import Configuration
from .parsing import create_parser
from .utils import _print_and_quit

# In practice, this dict will be overriden by _load_app
# but it is here to keep the linters happy and for testing
REGISTERED_COMMANDS: Dict[str, Callable] = {}

ReturnType = TypeVar("ReturnType")


def run_func_with_argv(
    function: Callable[..., ReturnType], argv: List[str], command: str
) -> ReturnType:
    parser = create_parser(function, command)
    args = parser.parse(argv)
    retval = function(**args)
    return retval


def run_func_with_argv_and_print(
    function: Callable[..., ReturnType], argv: List[str], command: str
) -> None:
    result = run_func_with_argv(function, argv, command)
    if result is not None:
        print(result)


def register_command(
    function: Union[str, Callable], name: Optional[str] = None
) -> None:
    """Register `function` as an available command"""
    # TODO(joris): Add custom types for arguments
    # TODO(joris): Add result formatter option
    python_function: Callable
    if isinstance(function, str):
        python_function = _get_function_from_str(function)
    else:
        python_function = function
    command_name = name or python_function.__name__
    # REGISTERED_COMMANDS is magically defined by _load_app
    REGISTERED_COMMANDS[command_name] = python_function


def register_app(name: str, location: Optional[Path] = None) -> None:
    """Register an app with auto_cli"""
    with Configuration() as config:
        config.register_app(name, location)


def run_command(app: str, argv: List[str]) -> None:
    """Run a command in app"""
    commands = _load_app(app)
    if len(argv) == 0:
        command_help = _command_help(commands)
        _print_and_quit(f"No command given. Available commands:\n{command_help}")
    command, *argv = argv
    function = commands[command]
    run_func_with_argv_and_print(function, argv, command)


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


def _load_app(name: str) -> Dict[str, Callable]:
    """Load the commands registered in auto_cli.py"""
    with Configuration() as config:
        ac_code = config.get_app_ac_content(name)
    ac_code = f"""
import auto_cli
auto_cli.cli.REGISTERED_COMMANDS = REGISTERED_COMMANDS
{ac_code}"""
    registered_commands: Dict[str, Callable] = {}
    exec(ac_code, {"REGISTERED_COMMANDS": registered_commands})
    return registered_commands


def _command_help(commands: Dict[str, Callable]) -> str:
    longest_name = max(map(len, commands))
    return "\n".join(
        f"{name.ljust(longest_name)}{_function_help(function)}"
        for name, function in commands.items()
    )


def _function_help(function: Callable) -> str:
    if function.__doc__ is not None:
        return "    " + function.__doc__
    return ""
