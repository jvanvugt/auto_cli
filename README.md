# auto_cli
auto_cli is a tool for calling Python functions directly from the command-line, without the need for writing argument parsers. Instead, the argument parser is automatically generated from the annotation of the function, including default arguments and types. When you use auto_cli, you can still use your Python functions from code without any changes. In fact, you can use auto_cli to generate a CLI for functions in a loose file, or for an external library, as long as the functions have type annotations.

## Getting Started
Add a file called `auto_cli.py` to any directory. This file registers all the functions that are available from the command-line. Register your command-line app with auto_cli, using
```
$ ac cli register_app --name my_app
```

Add any function you want to be able to call from the command-line to `auto_cli.py`. Here is a very simple `auto_cli.py`:

```python
import auto_cli

auto_cli.register_command("my_cool_package.get_weather")
```

Now, you can call your function from the command-line:
```
$ ac my_app get_weather --location Amsterdam
21 degrees celsius. Sunny all day!
```

## Benefits
- Write your function once, call it from Python code _and_ the command-line
- Automatically generate argument parsers, no need to duplicate argument names, default values, documentation and types.
- Automatically print the result of the function to the console, no need to clutter your code with `print` or `log`.
- Keep your production code free of decorators to describe command-line interfaces.
- Easily view all the available commands for your app.
