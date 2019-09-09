from setuptools import setup

setup(
    name="auto_cli",
    packages=[],
    version="0.1.0",
    description="Automatically generate a command-line interface for any Python function",
    author="Joris van Vugt",
    license="MIT",
    author_email="jorisvanvugt@gmail.com",
    url="https://github.com/jvanvugt/auto_cli",
    keywords=["cli", "command", "line", "interface"],
    classifiers=[],
    entry_points={"console_scripts": ["ac=auto_cli.cli:run"]},
)
