# temptf

[![PyPI version](https://img.shields.io/pypi/v/temptf.svg)](https://pypi.org/project/temptf/)
[![Python versions](https://img.shields.io/pypi/pyversions/temptf.svg)](https://pypi.org/project/temptf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Python client library for the [temp.tf](https://temp.tf/) disposable email API. Zero external dependencies.

## Installation

```bash
pip install temptf
```

## Quick Start

### Creating Addresses by Provider

```python
import temptf

# Random address across all providers
email = temptf.create_email()

# Provider-specific addresses
gmail_any = temptf.create_gmail()          # @gmail.com (dot or plus)
gmail_dot = temptf.create_gmail_dot()      # u.s.e.r@gmail.com
gmail_plus = temptf.create_gmail_plus()    # user+tag@gmail.com
outlook = temptf.create_outlook()          # user+tag@outlook.com
hotmail = temptf.create_hotmail()          # user+tag@hotmail.com
edu = temptf.create_edu()                  # @high.edu.pl
```

### Reading and Streaming Messages

```python
import temptf

email = temptf.create_outlook()
print("Listening on:", email)

# Fetch current inbox contents once
messages = temptf.get_messages(email)

# Block until the first matching message arrives
msg = temptf.wait_for_message(email, timeout=60.0)
print(msg.subject, msg.text)

# Stream incoming messages continuously
for msg in temptf.stream_messages(email, interval=5.0):
    print(f"[{msg.date}] {msg.sender}: {msg.subject}")
    print(msg.text)
```

### Using `TempTFClient` Directly

```python
from temptf import TempTFClient

client = TempTFClient(timeout=10.0)
email = client.create_gmail_plus()

for msg in client.stream_messages(email):
    for att in msg.attachments:
        client.download_attachment(email, msg.id, att.id, dest=f"./downloads/{att.name}")
```

## License

MIT
