import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple, Union

from .exceptions import APIError, RateLimitError, TempTFError
from .models import Message, Stats

BASE_URL = "https://temp.tf/api"
PROVIDERS = ("gmail", "outlook", "hotmail", "high.edu.pl")


class TempTFClient:
    """Client for the temp.tf disposable email API."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = 15.0,
        auto_retry_rate_limit: bool = True,
        user_agent: str = "temptf-python/0.1.0",
        opener: Optional[urllib.request.OpenerDirector] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.auto_retry_rate_limit = auto_retry_rate_limit
        self.user_agent = user_agent
        self._opener = opener or urllib.request.build_opener()

    def _request_raw(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, Dict[str, str]]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"

        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        data: Optional[bytes] = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        while True:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with self._opener.open(req, timeout=self.timeout) as resp:
                    resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                    return resp.read(), resp_headers
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw_err = exc.read()
                if status == 429:
                    retry_header = exc.headers.get("Retry-After") if exc.headers else None
                    retry_after = int(retry_header) if retry_header and retry_header.isdigit() else 5
                    if self.auto_retry_rate_limit:
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError(retry_after=retry_after) from exc

                try:
                    parsed = json.loads(raw_err.decode("utf-8", errors="replace"))
                    err_msg = parsed.get("error", raw_err.decode("utf-8", errors="replace"))
                except ValueError:
                    err_msg = raw_err.decode("utf-8", errors="replace")
                raise APIError(status, str(err_msg)) from exc
            except urllib.error.URLError as exc:
                raise TempTFError(f"Network error: {exc.reason}") from exc

    def _request_json(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raw, _ = self._request_raw(method, endpoint, params=params, json_body=json_body)
        try:
            return dict(json.loads(raw.decode("utf-8")))
        except ValueError as exc:
            raise TempTFError("Invalid JSON response from server") from exc

    def create_email(
        self,
        providers: Optional[Union[str, Sequence[str]]] = None,
        dot: bool = True,
        plus: bool = True,
    ) -> str:
        """Generate a random temporary email address."""
        if not dot and not plus:
            raise ValueError("At least one of 'dot' or 'plus' must be True.")

        params: Dict[str, str] = {}
        if dot:
            params["dot"] = "1"
        if plus:
            params["plus"] = "1"

        if providers:
            params["providers"] = (
                providers if isinstance(providers, str) else ",".join(providers)
            )

        payload = self._request_json("GET", "/account", params=params)
        email = payload.get("email")
        if not email:
            raise TempTFError("No email returned for the requested parameters.")
        return str(email)

    def create_gmail(self, dot: bool = True, plus: bool = True) -> str:
        """Generate a @gmail.com address using dot syntax, plus alias, or both."""
        return self.create_email(providers="gmail", dot=dot, plus=plus)

    def create_gmail_dot(self) -> str:
        """Generate a @gmail.com dot-variant address (e.g. u.s.e.r@gmail.com)."""
        return self.create_email(providers="gmail", dot=True, plus=False)

    def create_gmail_plus(self) -> str:
        """Generate a @gmail.com plus-alias address (e.g. user+tag@gmail.com)."""
        return self.create_email(providers="gmail", dot=False, plus=True)

    def create_outlook(self) -> str:
        """Generate an @outlook.com plus-alias address."""
        return self.create_email(providers="outlook", dot=False, plus=True)

    def create_hotmail(self) -> str:
        """Generate a @hotmail.com plus-alias address."""
        return self.create_email(providers="hotmail", dot=False, plus=True)

    def create_edu(self) -> str:
        """Generate a @high.edu.pl educational email address."""
        return self.create_email(providers="high.edu.pl", dot=False, plus=True)

    def get_messages(self, email: str) -> List[Message]:
        """Fetch all messages currently in the inbox for the given address."""
        payload = self._request_json("POST", "/check", json_body={"email": email})
        items = payload.get("data") or []
        return [Message.from_dict(item) for item in items]

    def wait_for_message(
        self,
        email: str,
        timeout: float = 120.0,
        interval: float = 4.0,
        predicate: Optional[Callable[[Message], bool]] = None,
    ) -> Message:
        """Poll the inbox until a matching message arrives or timeout is reached."""
        deadline = time.monotonic() + timeout
        while True:
            for msg in self.get_messages(email):
                if predicate is None or predicate(msg):
                    return msg
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for message on {email}")
            time.sleep(interval)

    def stream_messages(
        self,
        email: str,
        interval: float = 5.0,
        skip_existing: bool = False,
    ) -> Iterator[Message]:
        """Continuously poll the inbox and yield new messages as they arrive."""
        seen: Set[str] = set()
        if skip_existing:
            for msg in self.get_messages(email):
                seen.add(msg.id or f"{msg.date}:{msg.subject}")

        while True:
            messages = self.get_messages(email)
            for msg in reversed(messages):
                key = msg.id or f"{msg.date}:{msg.subject}"
                if key not in seen:
                    seen.add(key)
                    yield msg
            time.sleep(interval)

    def download_attachment(
        self,
        email: str,
        message_id: str,
        attachment_id: str,
        dest: Optional[Union[str, Path]] = None,
    ) -> bytes:
        """Download attachment content and optionally write it to disk."""
        params = {
            "email": email,
            "messageId": message_id,
            "attachmentId": attachment_id,
        }
        content, _ = self._request_raw("GET", "/attachment", params=params)
        if dest is not None:
            path = Path(dest)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return content

    def get_stats(
        self,
        providers: Optional[Union[str, Sequence[str]]] = None,
        dot: bool = True,
        plus: bool = True,
    ) -> Stats:
        """Return pool availability and message statistics."""
        params: Dict[str, str] = {}
        if dot:
            params["dot"] = "1"
        if plus:
            params["plus"] = "1"
        if providers:
            params["providers"] = (
                providers if isinstance(providers, str) else ",".join(providers)
            )
        payload = self._request_json("GET", "/stats", params=params)
        return Stats.from_dict(payload)
