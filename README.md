# SocialFlow

### AI-Powered Social Media Automation Platform

SocialFlow is an independent, self-hosted portfolio project for researching, planning, creating, reviewing, scheduling, publishing, and analyzing social-media content through an AI-assisted workflow.

> **Portfolio project:** Built by **Akinola Ayomide Daniel** to demonstrate practical software-engineering skills. It is not presented as commercial employment, client work, or proof that every third-party integration is production-ready.

## Core workflow

```text
Scout → Planner → Creator → Reviewer → Publisher → Analyst
```

| Stage | Responsibility |
|---|---|
| **Scout** | Collects trends, feeds, and other content signals |
| **Planner** | Turns signals into topics, platforms, formats, and publishing plans |
| **Creator** | Generates platform-specific copy and creative assets |
| **Reviewer** | Applies quality, brand, safety, and approval checks |
| **Publisher** | Publishes approved content through configured integrations |
| **Analyst** | Stores performance data and produces useful insights |

## Engineering highlights

- AI provider abstraction for Ollama, OpenAI, Anthropic, and Gemini
- FastAPI REST backend with OpenAPI/Swagger documentation
- Multi-stage workflow orchestration with explicit content states
- Scheduled automation support
- Browser automation with Playwright
- Platform-specific content generation
- Brand-kit and asset-management features
- Image/video workflow support
- SQLite persistence for local/self-hosted deployments
- Fernet encryption for locally stored platform credentials
- X OAuth 2.0 flow with signed state and PKCE
- Analytics and audit-oriented data storage
- Vercel-compatible API entry point
- CI integrity checks and Python compilation checks

## Integrations

The codebase contains integration logic for services including LinkedIn, X/Twitter, Facebook, Instagram, Discord, Reddit, Medium, Substack, HeyGen, beehiiv, MailerLite, and Brevo.

**Important:** an integration existing in the repository does not mean its external account, API access, browser flow, credentials, or current platform policies are configured. Third-party interfaces can change. Verify each integration in the target environment before relying on it.

## Architecture

```text
                         ┌───────────────┐
                         │   Dashboard   │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │  FastAPI API  │
                         └───────┬───────┘
                                 │
                  ┌──────────────┼──────────────┐
                  ▼              ▼              ▼
             AI Providers   Pipeline Agents   SQLite
                                 │
                         Scout → Planner
                                 ↓
                              Creator
                                 ↓
                              Reviewer
                                 ↓
                             Publisher
                                 ↓
                              Analyst
```

## API highlights

| Endpoint | Method | Purpose |
|---|---:|---|
| `/api/health` | GET | Server health check |
| `/api/pipeline/run` | POST | Run the content pipeline |
| `/api/pipeline/status` | GET | Read pipeline state |
| `/api/pipeline/queue` | GET | View queued content |
| `/api/pipeline/approve/{id}` | POST | Approve a draft |
| `/api/pipeline/reject/{id}` | POST | Reject a draft |
| `/api/pipeline/publish/{id}` | POST | Publish an approved item |
| `/api/pipeline/signals` | GET | Read discovery signals |
| `/api/pipeline/analytics` | GET | Read analytics |
| `/api/brand/config` | GET/PUT | Manage brand settings |
| `/api/accounts` | GET/POST | Manage connected accounts |
| `/api/posts` | GET/POST | Manage posts |
| `/docs` | GET | Swagger/OpenAPI documentation |

## Security model

- Secrets are supplied through environment variables and excluded from Git.
- `.env`, generated encryption keys, databases, browser sessions, uploads, and logs are ignored by Git.
- Platform credentials handled by the application are encrypted with Fernet at rest.
- X uses OAuth 2.0 with PKCE rather than requesting an X password.
- Publishing can be gated by approval/rejection workflow states.
- CI checks the repository for common accidentally committed API-key patterns.

**Never commit API keys, OAuth client secrets, passwords, cookies, browser profiles, session files, `.secret_key`, or real user data.** If a real secret is ever exposed, rotate it immediately; deleting the file alone is not sufficient.

See [`SECURITY.md`](SECURITY.md) for the repository security policy.

## Quick start

```bash
git clone https://github.com/Dannygray29/SocialFlow.git
cd SocialFlow/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python main.py
```

Then open `http://localhost:8000` and use `/docs` for the API documentation.

For local AI, configure `.env` using the supplied `.env.example`:

```env
AI_PROVIDER=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
HEADLESS=false
```

## Development checks

The repository includes automated integrity checks under `tests/` and GitHub Actions.

```bash
pip install pytest
pytest -q
python -m compileall -q backend api
```

The checks validate that required project files exist, Python sources parse successfully, and obvious credential patterns are not committed. These are smoke/integrity checks—not a claim of complete end-to-end verification of every external social platform.

## Technology stack

- Python 3
- FastAPI
- SQLite
- APScheduler
- Playwright / Chromium
- React-based browser frontend
- HTTPX
- Pydantic
- Fernet cryptography
- Ollama / OpenAI / Anthropic / Gemini
- Pillow
- FFmpeg
- GitHub Actions

## Skills demonstrated

This project demonstrates practical work in AI application architecture, LLM integration, REST APIs, Python backend engineering, browser automation, OAuth/PKCE, credential handling, workflow orchestration, database persistence, scheduled jobs, analytics, testing, CI, and product-focused problem solving.

## Integrity standard

**Goal: production-quality engineering discipline, with honest status reporting.**

A green CI run means the repository's automated smoke checks passed. It does **not** mean every external API, browser selector, credential configuration, or deployment environment is guaranteed to work. SocialFlow intentionally documents that distinction rather than making unsupported 100% claims.

## License

MIT License — see [`LICENSE`](LICENSE).

## Author

**Akinola Ayomide Daniel**

Independent developer building practical projects in AI, automation, software engineering, cybersecurity, and digital products.
