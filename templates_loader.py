import re
from fastapi.templating import Jinja2Templates


def _js_escape(value: str | None) -> str:
    """Escape a string for safe embedding inside a JavaScript single-quoted
    string literal.  Produces a value where every backslash and single quote
    is backslash-escaped so that ``'…'`` is never broken by user content."""
    if value is None:
        return ""
    s = str(value)
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    return s


templates = Jinja2Templates(directory="templates")
templates.env.filters["js_escape"] = _js_escape


def get_templates() -> Jinja2Templates:
    return templates
