from auto_cli.cli import run_func_with_argv


def test_run_func_with_argv() -> None:
    def func_to_test(a: int, b: int = 38) -> int:
        return a + b

    result = run_func_with_argv(func_to_test, ["--a", "4"])
    assert result == 42
