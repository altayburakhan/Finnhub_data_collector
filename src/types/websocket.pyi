"""WebSocket type stub file."""

from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T", bound="WebSocketApp")

class WebSocketApp:
    def __init__(
        self,
        url: str,
        header: Optional[dict] = None,
        on_open: Optional[Callable[[T], None]] = None,
        on_message: Optional[Callable[[T, str], None]] = None,
        on_error: Optional[Callable[[T, str], None]] = None,
        on_close: Optional[Callable[[T, Optional[int], Optional[str]], None]] = None,
        on_ping: Optional[Callable[[T, Any], None]] = None,
        on_pong: Optional[Callable[[T, Any], None]] = None,
        on_cont_message: Optional[Callable[[T, Any, Any], None]] = None,
        on_data: Optional[Callable[[T, Any, Any, Any], None]] = None,
        keep_running: bool = True,
        get_mask_key: Optional[Callable[[], Any]] = None,
        cookie: Optional[str] = None,
        subprotocols: Optional[list] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...
    def run_forever(self, *args: Any, **kwargs: Any) -> None: ...
    def send(self, data: str, opcode: int = ...) -> None: ...
    def close(self) -> None: ...

def enableTrace(traceable: bool) -> None: ...
