from typing import Callable, Iterator, List, Optional, Sequence, Union

from .client import PROVIDERS, TempTFClient
from .exceptions import APIError, RateLimitError, TempTFError
from .models import Attachment, Message, Stats

__version__ = "0.1.0"

_default_client: Optional[TempTFClient] = None


def _get_client() -> TempTFClient:
    global _default_client
    if _default_client is None:
        _default_client = TempTFClient()
    return _default_client


def create_email(
    providers: Optional[Union[str, Sequence[str]]] = None,
    dot: bool = True,
    plus: bool = True,
) -> str:
    """Generate a random temporary email address."""
    return _get_client().create_email(providers=providers, dot=dot, plus=plus)


def create_gmail(dot: bool = True, plus: bool = True) -> str:
    """Generate a @gmail.com address using dot syntax, plus alias, or both."""
    return _get_client().create_gmail(dot=dot, plus=plus)


def create_gmail_dot() -> str:
    """Generate a @gmail.com dot-variant address."""
    return _get_client().create_gmail_dot()


def create_gmail_plus() -> str:
    """Generate a @gmail.com plus-alias address."""
    return _get_client().create_gmail_plus()


def create_outlook() -> str:
    """Generate an @outlook.com address."""
    return _get_client().create_outlook()


def create_hotmail() -> str:
    """Generate a @hotmail.com address."""
    return _get_client().create_hotmail()


def create_edu() -> str:
    """Generate a @high.edu.pl address."""
    return _get_client().create_edu()


def get_messages(email: str) -> List[Message]:
    """Fetch all messages in the inbox for the given address."""
    return _get_client().get_messages(email)


def wait_for_message(
    email: str,
    timeout: float = 120.0,
    interval: float = 4.0,
    predicate: Optional[Callable[[Message], bool]] = None,
) -> Message:
    """Poll the inbox until a message arrives or timeout expires."""
    return _get_client().wait_for_message(
        email=email,
        timeout=timeout,
        interval=interval,
        predicate=predicate,
    )


def stream_messages(
    email: str,
    interval: float = 5.0,
    skip_existing: bool = False,
) -> Iterator[Message]:
    """Yield new messages for the given address as they arrive."""
    return _get_client().stream_messages(
        email=email,
        interval=interval,
        skip_existing=skip_existing,
    )


def get_stats(
    providers: Optional[Union[str, Sequence[str]]] = None,
    dot: bool = True,
    plus: bool = True,
) -> Stats:
    """Return pool availability and message statistics."""
    return _get_client().get_stats(providers=providers, dot=dot, plus=plus)


__all__ = [
    "__version__",
    "PROVIDERS",
    "TempTFClient",
    "TempTFError",
    "APIError",
    "RateLimitError",
    "Message",
    "Attachment",
    "Stats",
    "create_email",
    "create_gmail",
    "create_gmail_dot",
    "create_gmail_plus",
    "create_outlook",
    "create_hotmail",
    "create_edu",
    "get_messages",
    "wait_for_message",
    "stream_messages",
    "get_stats",
]
