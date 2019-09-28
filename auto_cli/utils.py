import sys


def _make_red(text: str) -> str:
    red_code = "\033[91m"
    end_code = "\033[0m"
    return f"{red_code}{text}{end_code}"


def _print_and_quit(message: str, is_error: bool = True) -> None:
    """Write message to sys.stdout and quit with exit code 1"""
    if is_error:
        print(_make_red("Error:"), end=" ")
    print(message)
    sys.exit(1)
