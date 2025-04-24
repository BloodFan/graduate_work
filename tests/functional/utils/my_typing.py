from typing import Any, Awaitable, Callable

from multidict import CIMultiDictProxy
from yarl import URL

FuncType = Callable[
    [str, dict], Awaitable[tuple[dict[str, Any], CIMultiDictProxy, URL, int]]
]
