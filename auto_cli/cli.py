import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union


CONFIG_FILE = Path("~/.auto_cli").expanduser()
REGISTERED_COMMANDS: Dict[str, Callable] = {}

ReturnType = TypeVar("ReturnType")


def run_func_with_argv(
    function: Callable[..., ReturnType], argv: List[str]
) -> ReturnType:
    parser = _create_parser(function)
    args = parser.parse_args(argv)
    retval = function(**vars(args))
    return retval


def run_func_with_argv_and_print(
    function: Callable[..., ReturnType], argv: List[str]
) -> None:
    result = run_func_with_argv(function, argv)
    if result is not None:
        print(result)


def register_command(
    function: Union[str, Callable], name: Optional[str] = None
) -> None:
    """Register `function` as an available command"""
    python_function: Callable
    if isinstance(function, str):
        python_function = _get_function_from_str(function)
    else:
        python_function = function
    command_name = name or python_function.__name__
    REGISTERED_COMMANDS[command_name] = python_function


def register_app(name: str, location: Optional[Path] = None) -> None:
    """Register an app with auto_cli"""
    with _Configuration() as config:
        config.register_app(name, location)


def run_command(app: str, argv: List[str]) -> None:
    """Run a command in app"""
    _load_app(app)
    if len(argv) == 0:
        _print_and_quit(f"No command given. Available commands:\n{_command_help()}")
    command, *argv = argv
    function = REGISTERED_COMMANDS[command]
    run_func_with_argv_and_print(function, argv)


def run() -> None:
    """Main entrypoint for auto_cli, run an app and command based on sys.argv"""
    if len(sys.argv) < 2:
        _print_and_quit(
            "Did not understand command.\nUsage: az <app> <command> [paramaters]"
        )
    app = sys.argv[1]
    run_command(app, sys.argv[2:])


def apps() -> List[str]:
    """Get all registered apps"""
    with _Configuration() as config:
        return config.get_apps()


class _Configuration:
    """Interface for interacting with auto_cli's configuration"""

    def __init__(self, config_path: Path = CONFIG_FILE):
        if config_path.exists():
            with config_path.open() as fp:
                self.config = json.load(fp)
        else:
            self.config = {"apps": {}}
        self._config_path = config_path
        self._dirty = False

    def register_app(self, name: str, location: Optional[Path]) -> None:
        """Register an app called `name` located at `location`"""
        if " " in name:
            _print_and_quit("Spaces are not allowed in the app name")

        app_location = Path.cwd() if location is None else location.resolve()
        ac_file = app_location / "auto_cli.py"
        if not ac_file.exists():
            _print_and_quit(f"Can not find {ac_file}")

        self.config["apps"][name] = {"location": str(app_location)}
        self._dirty = True

    def get_app_location(self, name: str) -> Path:
        """Get the location of the app called `name`"""
        location = self.config["apps"].get(name)
        if location is None:
            # TODO(joris): "Did you mean?", "You can register..."
            _print_and_quit(f"Unknown app '{name}'.")
        return Path(location)

    def get_app_ac_content(self, name: str) -> str:
        """Get the content of auto_cli.py for app `name`"""
        location = self.get_app_location(name)
        ac_file = location / "auto_cli.py"
        if not ac_file.exists():
            _print_and_quit(f"Could not find auto_cli file {ac_file}. Was it deleted?")
        return ac_file.read_text()

    def get_apps(self) -> List[str]:
        """Get a list of all registered apps"""
        return list(self.config["apps"].keys())

    def __enter__(self) -> "Configuration":
        return self

    def __exit__(self, *args: Any) -> None:
        if self._dirty:
            with self._config_path.open("w") as fp:
                json.dump(self.config, fp, indent=4, sort_keys=True)


def _create_parser(function: Callable) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{function.__name__}: {function.__doc__}"
    )
    signature = inspect.signature(function)

    for param_name, parameter in signature.parameters.items():
        required = not _has_default(parameter)
        default = parameter.default if _has_default(parameter) else None
        type_ = _get_param_type(parameter.annotation, param_name, function)

        # TODO(joris): Deal with List, Tuple
        parser.add_argument(
            f"--{param_name}", type=type_, required=required, default=default
        )
        # TODO(joris): parse documentation of param for help

    return parser


def _print_and_quit(message: str) -> None:
    """Write message to sys.stdout and quit with exit code 1"""
    print(_make_red("Error:"), message)
    sys.exit(1)


def _has_default(parameter: inspect.Parameter) -> bool:
    """Check if parameter has a default value"""
    return parameter.default != inspect.Parameter.empty


def _get_param_type(annotation: Any, param_name: str, function: Callable) -> Callable:
    def _fail(message: str) -> None:
        _print_and_quit(
            f"Error processing paramter '{param_name}' "
            f"with type {annotation} of '{function}': {message}"
        )

    annotation_type = type(annotation)
    if annotation_type is Union:
        args = annotation.__args__
        if len(args) == 2 and args[1] is type(None):  # Optional
            return args[0]
        else:
            _fail(f"Unions are not supported")

    return annotation


def _get_function_from_str(path: str) -> Callable:
    """Return the Python function pointed to by `path`"""
    module_name, _, function_name = path.rpartition(".")
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    return function


def _load_app(name: str) -> None:
    """Load app into `REGISTERED_COMMANDS`"""
    with _Configuration() as config:
        ac_code = config.get_app_ac_content(name)
    exec(ac_code)


def _command_help() -> str:
    longest_name = max(map(len, REGISTERED_COMMANDS))
    return "\n".join(
        f"{name.ljust(longest_name)}{_function_help(function)}"
        for name, function in REGISTERED_COMMANDS.items()
    )


def _function_help(function) -> str:
    if function.__doc__ is not None:
        return "    " + function.__doc__
    return ""


def _make_red(text: str) -> str:
    red_code = "\033[91m"
    end_code = "\033[0m"
    return f"{red_code}{text}{end_code}"
