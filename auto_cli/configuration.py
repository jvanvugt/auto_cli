import json
import os
from pathlib import Path
from typing import Any, List, Optional

from .utils import _print_and_quit

CONFIG_FILE = os.environ.get("AUTO_CLI_CONFIG_FILE", Path("~/.auto_cli").expanduser())


class Configuration:
    """Interface for interacting with auto_cli's configuration"""

    def __init__(self, config_path: Path = CONFIG_FILE):
        self._dirty = False
        if config_path.exists():
            with config_path.open() as fp:
                self.config = json.load(fp)
        else:
            # By default register auto_cli itself
            self.config = {"apps": {"cli": str(Path(__file__).parent.parent)}}
            self._dirty = True
        self._config_path = config_path

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

    def delete_app(self, name: str) -> None:
        apps = self.config["apps"]
        if name not in apps:
            _print_and_quit(
                f"Unknown app '{name}'. Run `ac cli apps` to see which apps are registered."
            )
        del apps[name]
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
        file_content = ac_file.read_text()

        # Already do a dry-run of the file to check for errors
        code = compile(file_content, str(ac_file), "exec")
        exec(code)

        return file_content

    def get_apps(self) -> List[str]:
        """Get a list of all registered apps"""
        return list(self.config["apps"].keys())

    def __enter__(self) -> "Configuration":
        return self

    def __exit__(self, *args: Any) -> None:
        if self._dirty:
            with self._config_path.open("w") as fp:
                json.dump(self.config, fp, indent=4, sort_keys=True)
