from typing import Any, Callable, Dict, NamedTuple, Optional


class Command(NamedTuple):
    name: str
    function: Callable[..., Any]
    parameter_types: Optional[Dict[str, Callable]]
    return_type: Optional[Callable[[Any], Any]]

    @staticmethod
    def from_func(function: Callable, name: Optional[str] = None) -> "Command":
        """Convience function for what should be the most common case:
        Creating a Command from a Python function with no bells or whistles
        """
        return Command(name or function.__name__, function, None, None)
