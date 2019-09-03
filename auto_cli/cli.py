import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union


CONFIG_FILE = Path("~/.auto_cli").expanduser()
REGISTERED_COMMANDS: Dict[str, Callable] = {}


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


def register_command(
    function: Union[str, Callable], name: Optional[str] = None
) -> None:
    command_name = name or function.__name__
    REGISTERED_COMMANDS[command_name] = function


def register_cli(name: str, location: Path) -> None:
    with Configuration() as config:
        config.register_cli(name, location)


def run_command(cli: str, command: List[str]) -> None:
    with Configuration() as config:
        location = config.get_cli_location(cli)
        ac_file = location / "auto_cli.py"
        if not ac_file.exists():
            raise RuntimeError(
                f"Could not find auto_cli file {ac_file}. Was it deleted?"
            )
        exec(ac_file.read_text())
        command, *argv = command
        function = REGISTERED_COMMANDS[command]
        run_func_with_argv_and_print(function, argv)


def run() -> None:
    if len(sys.argv) < 3:
        # TODO(joris): Add good error messages
        raise ValueError("")
    cli = sys.argv[1]
    run_command(cli, sys.argv[2:])


class Configuration:
    def __init__(self, config_path: Path = CONFIG_FILE):
        if config_path.exists():
            with config_path.open() as fp:
                self.config = json.load(fp)
        else:
            self.config = {"clis": {}}
        self._config_path = config_path
        self._dirty = False

    def register_cli(self, name: str, location: Path) -> None:
        if " " in name:
            raise ValueError("Spaces are not allowed in the cli name")

        self.config["clis"][name] = {"location": str(location.resolve())}
        self._dirty = True

    def get_cli_location(self, name: str) -> Path:
        location = self.config["clis"].get(name)
        if location is None:
            # TODO(joris): "Did you mean?", "You can register..."
            raise ValueError(f"Unknown cli '{name}'.")
        return Path(location)

    def __enter__(self) -> "Configuration":
        return self

    def __exit__(self, *args: Any) -> None:
        if self._dirty:
            with self._config_path.open("w") as fp:
                json.dump(self.config, fp, indent=4, sort_keys=True)
