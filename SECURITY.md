# Security Policy

SocialFlow is a fork-derived portfolio project maintained by Akinola Ayomide Daniel. Do not use real production credentials or personal account sessions while testing it.

## Reporting a vulnerability

Please do not publish credentials, session files, access tokens, or other sensitive data in an issue. If this repository is used beyond local development, report security concerns privately through the repository owner's GitHub contact channel.

## Security expectations

- Keep `.env` and `.secret_key` out of version control.
- Never commit API keys, OAuth client secrets, cookies, browser profiles, or session data.
- Use OAuth integrations where supported instead of collecting platform passwords.
- Treat browser automation credentials as sensitive even when encrypted at rest.
- Rotate any credential that may have been exposed.

The repository's CI includes lightweight checks for common accidentally committed API-key patterns. Those checks are not a substitute for secret scanning, dependency auditing, or a security review before production use.
