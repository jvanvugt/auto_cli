import sys


def _make_red(text: str) -> str:
    red_code = "\033[91m"
    end_code = "\033[0m"
    return f"{red_code}{text}{end_code}"


def _print_and_quit(message: str) -> None:
    """Write message to sys.stdout and quit with exit code 1"""
    print(_make_red("Error:"), message)
    sys.exit(1)
