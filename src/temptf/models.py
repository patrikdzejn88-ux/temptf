import html
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = html.unescape(cleaned)
    return "\n".join(line.strip() for line in cleaned.splitlines() if line.strip())


@dataclass(frozen=True)
class Attachment:
    id: str
    name: str
    content_type: str
    size: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            content_type=str(data.get("contentType", "application/octet-stream")),
            size=int(data.get("size", 0)),
        )


@dataclass(frozen=True)
class Message:
    id: str
    sender: str
    subject: str
    date: str
    body: str
    body_content_type: str
    attachments: List[Attachment] = field(default_factory=list)
    inline_cids: Dict[str, str] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Plain-text representation of the message body."""
        if self.body_content_type.lower() == "html":
            return _strip_html(self.body)
        return self.body.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        attachments = [Attachment.from_dict(item) for item in (data.get("attachments") or [])]
        return cls(
            id=str(data.get("id", "")),
            sender=str(data.get("from", "")),
            subject=str(data.get("subject", "")),
            date=str(data.get("date", "")),
            body=str(data.get("body", "")),
            body_content_type=str(data.get("bodyContentType", "text")),
            attachments=attachments,
            inline_cids=dict(data.get("inlineCids") or {}),
        )


@dataclass(frozen=True)
class Stats:
    total_addresses: int
    total_formatted: str
    total_received: int
    breakdown: Dict[str, int]
    breakdown_formatted: Dict[str, str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stats":
        raw_breakdown = data.get("breakdown") or {}
        breakdown = {k: int(v) for k, v in raw_breakdown.items()}
        return cls(
            total_addresses=int(data.get("totalAddresses", 0)),
            total_formatted=str(data.get("totalFormatted", "0")),
            total_received=int(data.get("totalReceived", 0)),
            breakdown=breakdown,
            breakdown_formatted=dict(data.get("breakdownFormatted") or {}),
        )
