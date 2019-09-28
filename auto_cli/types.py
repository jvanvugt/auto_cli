import re
from typing import Any, Callable, Dict, NamedTuple, Optional


class FunctionDoc(NamedTuple):
    description: str
    param_docs: Dict[str, str]


class Command(NamedTuple):
    name: str
    function: Callable[..., Any]
    parameter_types: Optional[Dict[str, Callable]] = None
    return_type: Optional[Callable[[Any], Any]] = None
    short_names: Optional[Dict[str, str]] = None

    @staticmethod
    def from_func(function: Callable, name: Optional[str] = None) -> "Command":
        """Convience function for what should be the most common case:
        Creating a Command from a Python function with no bells or whistles
        """
        return Command(name or function.__name__, function)

    def parse_function_doc(self) -> FunctionDoc:
        """Parse function documentation which adheres to the Sphinx standard
        https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#info-field-lists
        """
        function = self.function
        if not hasattr(function, "__doc__") or function.__doc__ is None:
            return FunctionDoc("", {})

        doc = function.__doc__
        if not ":param" in doc:
            # Doesn't conform to our standard, so the whole __doc__ is just
            # the description of the function
            return FunctionDoc(doc, {})

        # Now that we know doc conforms to our standard, we can extract the
        # parameter descriptions
        params_docs = {}
        for line in doc.splitlines():
            line = line.strip()
            if line.startswith(":param"):
                line = line.lstrip(":param")
                before, _, description = line.partition(":")
                param_name = before.strip().split(" ")[-1]
                params_docs[param_name] = description.strip()

        fn_description, _, _ = doc.partition(":param")
        fn_description = _normalize_whitespace(fn_description.strip())
        return FunctionDoc(fn_description, params_docs)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)
