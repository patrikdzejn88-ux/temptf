import io
import json
import unittest
import urllib.error
from email.message import Message as HTTPHeaders
from unittest.mock import MagicMock

from temptf import TempTFClient
from temptf.exceptions import APIError, RateLimitError


def _mock_opener(payload=None, raw_bytes: bytes = b""):
    opener = MagicMock()
    resp = MagicMock()
    if payload is not None:
        raw_bytes = json.dumps(payload).encode("utf-8")
    resp.read.return_value = raw_bytes
    resp.headers = {"Content-Type": "application/json"}
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    opener.open.return_value = resp
    return opener


class TestTempTFClient(unittest.TestCase):
    def test_provider_specific_creation(self) -> None:
        opener = _mock_opener({"email": "u.s.e.r@gmail.com"})
        client = TempTFClient(opener=opener)

        self.assertEqual(client.create_gmail_dot(), "u.s.e.r@gmail.com")
        req = opener.open.call_args[0][0]
        self.assertEqual(req.full_url, "https://temp.tf/api/account?dot=1&providers=gmail")

        opener = _mock_opener({"email": "user+123@gmail.com"})
        client = TempTFClient(opener=opener)
        self.assertEqual(client.create_gmail_plus(), "user+123@gmail.com")
        req = opener.open.call_args[0][0]
        self.assertEqual(req.full_url, "https://temp.tf/api/account?plus=1&providers=gmail")

        opener = _mock_opener({"email": "user+123@outlook.com"})
        client = TempTFClient(opener=opener)
        self.assertEqual(client.create_outlook(), "user+123@outlook.com")
        req = opener.open.call_args[0][0]
        self.assertEqual(req.full_url, "https://temp.tf/api/account?plus=1&providers=outlook")

        opener = _mock_opener({"email": "user+123@hotmail.com"})
        client = TempTFClient(opener=opener)
        self.assertEqual(client.create_hotmail(), "user+123@hotmail.com")
        req = opener.open.call_args[0][0]
        self.assertEqual(req.full_url, "https://temp.tf/api/account?plus=1&providers=hotmail")

        opener = _mock_opener({"email": "abc@high.edu.pl"})
        client = TempTFClient(opener=opener)
        self.assertEqual(client.create_edu(), "abc@high.edu.pl")
        req = opener.open.call_args[0][0]
        self.assertEqual(req.full_url, "https://temp.tf/api/account?plus=1&providers=high.edu.pl")

    def test_get_messages_and_html_stripping(self) -> None:
        payload = {
            "data": [
                {
                    "id": "101",
                    "from": "noreply@service.com",
                    "subject": "Verification Code",
                    "date": "2026-11-06T12:00:00.000Z",
                    "body": "<html><body><p>Your code is <b>482910</b></p></body></html>",
                    "bodyContentType": "html",
                    "attachments": [
                        {
                            "id": "att_1",
                            "name": "receipt.pdf",
                            "contentType": "application/pdf",
                            "size": 512,
                        }
                    ],
                }
            ],
            "totalReceived": 500,
        }
        opener = _mock_opener(payload)
        client = TempTFClient(opener=opener)

        messages = client.get_messages("user+123@gmail.com")
        self.assertEqual(len(messages), 1)
        msg = messages[0]
        self.assertEqual(msg.id, "101")
        self.assertEqual(msg.sender, "noreply@service.com")
        self.assertEqual(msg.subject, "Verification Code")
        self.assertEqual(msg.text, "Your code is 482910")
        self.assertEqual(len(msg.attachments), 1)
        self.assertEqual(msg.attachments[0].name, "receipt.pdf")

    def test_error_handling(self) -> None:
        opener = MagicMock()
        client = TempTFClient(opener=opener, auto_retry_rate_limit=False)

        headers = HTTPHeaders()
        headers["Retry-After"] = "12"
        err_429 = urllib.error.HTTPError(
            url="https://temp.tf/api/check",
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=io.BytesIO(b'{"error":"Rate limit"}'),
        )
        opener.open.side_effect = err_429
        with self.assertRaises(RateLimitError) as exc_info:
            client.get_messages("user+123@gmail.com")
        self.assertEqual(exc_info.exception.retry_after, 12)

        err_403 = urllib.error.HTTPError(
            url="https://temp.tf/api/check",
            code=403,
            msg="Forbidden",
            hdrs=HTTPHeaders(),
            fp=io.BytesIO(b'{"error":"Forbidden address"}'),
        )
        opener.open.side_effect = err_403
        with self.assertRaises(APIError) as api_exc:
            client.get_messages("invalid@example.com")
        self.assertEqual(api_exc.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
