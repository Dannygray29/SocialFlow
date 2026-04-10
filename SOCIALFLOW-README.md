# SocialFlow — Multi-Platform Posting Engine

Browser-based social media automation using Playwright. Posts content like a human would — via actual browser sessions with your dedicated marketing account credentials.

## Supported Platforms (12)

| Platform | Login | Post | Session Persist | Method |
|----------|-------|------|-----------------|--------|
| LinkedIn | Yes | Yes | Yes | Browser |
| X / Twitter | Yes | Yes | Yes | Browser |
| Facebook | Yes | Yes | Yes | Browser |
| Instagram | Yes | Yes | Yes | Browser |
| Discord | N/A | Yes | N/A | Webhook |
| Reddit | Yes | Yes | Yes | Browser |
| Medium | Yes | Yes | Yes | Browser |
| Substack | Yes | Yes | Yes | Browser |
| HeyGen | Yes | Yes | Yes | Browser |
| beehiiv | Yes | Yes | Yes | Browser |
| MailerLite | Yes | Yes | Yes | Browser |
| Brevo | Yes | Yes | Yes | Browser |

## Quick Start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python main.py
# Server at http://localhost:8000
```

## Security

- Credentials encrypted with Fernet (AES-128-CBC)
- Browser sessions stored locally only
- No credentials transmitted externally
- All actions logged with timestamps
