"""Render diagnostic chains without exposing vendor response bodies or requests."""

import traceback

from shared.application.result import Error


def format_diagnostic_exception(error: BaseException) -> str:
    """Keep exception identity/cause objects intact; sanitize only their rendering."""
    seen: set[int] = set()

    def render(current: BaseException) -> str:
        if id(current) in seen:
            return "[exception chain cycle omitted]\n"
        seen.add(id(current))
        prefix = ""
        if current.__cause__ is not None:
            prefix = render(current.__cause__) + (
                "\nThe above exception was the direct cause of the following exception:\n\n"
            )
        elif current.__context__ is not None and not current.__suppress_context__:
            prefix = render(current.__context__) + (
                "\nDuring handling of the above exception, another exception occurred:\n\n"
            )
        kind = type(current)
        external = kind.__module__.split(".")[0] in {"openai", "httpx", "httpcore"}
        detail = "[external provider details omitted]" if external else str(current)
        stack = "".join(traceback.format_tb(current.__traceback__))
        text = prefix + ("Traceback (most recent call last):\n" + stack if stack else "")
        text += f"{kind.__module__}.{kind.__name__}: {detail}\n"
        if not external:
            for note in getattr(current, "__notes__", ()):
                text += f"{note}\n"
        if isinstance(current, BaseExceptionGroup):
            for child in current.exceptions:
                text += render(child)
        return text

    return Error.sanitize(render(error))
