# auto_cli

[![CircleCI](https://circleci.com/gh/jvanvugt/auto_cli.svg?style=svg)](https://circleci.com/gh/jvanvugt/auto_cli)
[![Documentation Status](https://readthedocs.org/projects/auto-cli/badge/?version=latest)](https://auto-cli.readthedocs.io/en/latest/?badge=latest)

`auto_cli` is a tool for calling Python functions directly from the command-line, without the need for writing argument parsers. Instead, the argument parser is automatically generated from the annotation of the function, including default arguments and types. When you use `auto_cli`, you can still use your Python functions from code without any changes. In fact, you can use `auto_cli` to generate a CLI for functions in a stand-alone script, or for an external library, as long as the functions have type annotations.


## Installation
auto_cli requires Python 3.6+ and can be installed as follows
```
$ git clone https://github.com/jvanvugt/auto_cli
$ pip install ./auto_cli
```

## Getting Started
Add a file called `auto_cli.py` to any directory. This file registers all the functions that are available from the command-line. Imagine you wrote a package called `weather`, containing just a single function with the signature
```python
def get_weather(location: str = "London") -> WeatherReport:
    ...
```

You can add a command-line interface for this function by making your `auto_cli.py` look like
```python
import auto_cli

auto_cli.register_command("weather.get_weather")
```

Register your command-line app with `auto_cli`, by running the following command from the directory with `auto_cli.py`:
```
$ ac cli register_app --name weather
```

All `auto_cli` commands start with `ac`. When you install `auto_cli`, the `cli` app will automatically be registered. The `cli` app is used for interacting with `auto_cli` itself. After running the command above, the commands that are registered in `auto_cli.py` are available via `ac weather <command>`.


Now, you can call your function from the command-line:
```bash
$ ac weather get_weather --location Amsterdam
21 degrees celsius. Sunny all day in Amsterdam!

$ ac weather get_weather  # It will use the default value for location
16 degrees celsius. Rainy all day in London!
```

Instead of giving a string to `register_command` (which is convenient when the package is installed), you can also give it the function object directly. That will allow you to create a CLI for functions in arbitrary Python scripts. Then your `auto_cli.py` would look like this:
```python
import auto_cli
from weather import get_weather

auto_cli.register_command(get_weather)
```

Alternatively, you could manipulate the `PYTHONPATH` environment variable to make sure Python can find your function.

## ac cli
The following commands are available with `ac cli`:
```
apps            Get all registered apps
register_app    Register an app with auto_cli
delete_app      Delete the app
```
In general, you can figure out which commands are available for an app by running
```
$ ac <app>
```

If you want to know how to use a command, you can run it with `--help`:
```
$ ac cli register_app --help
```

## Benefits over other CLI packages
- Write your function once, call it from Python code _and_ the command-line
- Automatically generate argument parsers, no need to duplicate argument names, default values, documentation and types.
- Automatically print the result of the function to the console, no need to clutter your code with `print` or `log`.
- Keep your production code free of decorators to describe command-line interfaces.
- Easily view all the available commands for your app.
