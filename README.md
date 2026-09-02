# SocialFlow

### AI-Powered Social Media Automation Platform

SocialFlow is a self-hosted social media automation project designed to turn a content idea or emerging trend into a structured workflow for research, planning, creation, review, publishing, and analytics.

> **Portfolio project:** Built as an independent software project to demonstrate practical skills in AI integration, automation, backend development, API design, security, and product engineering.

## What it does

SocialFlow is organized around a six-stage content pipeline:

```text
Scout → Planner → Creator → Reviewer → Publisher → Analyst
```

| Agent | Responsibility |
|---|---|
| **Scout** | Discovers news, trends, feeds, and relevant signals |
| **Planner** | Selects topics, platforms, formats, and publishing plans |
| **Creator** | Generates platform-specific content and creative assets |
| **Reviewer** | Applies quality, brand, safety, and claim checks |
| **Publisher** | Publishes approved content through supported integrations |
| **Analyst** | Collects performance information and produces insights |

## Key capabilities

- AI-assisted content generation
- Multi-provider AI support
- Autonomous content pipeline orchestration
- Scheduled content workflows
- Draft, approval, rejection, and publishing states
- Brand-kit configuration
- Platform-specific content generation
- Image and carousel generation
- Video/reel workflow support
- Browser automation with Playwright
- Local SQLite persistence
- Encrypted credential storage
- Analytics and reporting
- REST API with interactive documentation
- Local/self-hosted deployment

## AI providers

- **Ollama** — local AI inference
- **OpenAI** — API-based generation
- **Anthropic** — API-based generation
- **Google Gemini** — API-based generation

## Integrations

The repository contains integrations/workflows for services including LinkedIn, X/Twitter, Facebook, Instagram, Discord, Reddit, Medium, Substack, HeyGen, beehiiv, MailerLite, and Brevo. Availability and authentication requirements vary by integration and deployment configuration.

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
| `/api/pipeline/run` | POST | Run the autonomous pipeline |
| `/api/pipeline/status` | GET | Read pipeline state |
| `/api/pipeline/queue` | GET | View content queue |
| `/api/pipeline/approve/{id}` | POST | Approve a draft |
| `/api/pipeline/reject/{id}` | POST | Reject a draft |
| `/api/pipeline/publish/{id}` | POST | Publish a specific item |
| `/api/pipeline/signals` | GET | Read discovery signals |
| `/api/pipeline/analytics` | GET | Read performance analytics |
| `/api/brand/config` | GET/PUT | Manage brand settings |
| `/api/accounts` | GET/POST | Manage connected accounts |
| `/api/posts` | GET/POST | Manage posts |
| `/docs` | GET | Swagger/OpenAPI documentation |

## Security

- Platform credentials are encrypted locally using Fernet.
- Secrets should be supplied through environment variables rather than committed to Git.
- Browser sessions remain in the local deployment environment.
- Approval gates can stop content before publication.
- Actions can be recorded for auditing.

**Never commit `.env`, API keys, passwords, browser session data, private credentials, or generated secret keys.**

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

Configure a local `.env` file. For local AI:

```env
AI_PROVIDER=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
HEADLESS=false
```

FastAPI documentation is available at `/docs` after the server starts.

## Technology stack

- Python 3
- FastAPI
- SQLite
- APScheduler
- Playwright / Chromium
- React-based frontend
- HTTPX
- Pydantic
- Fernet cryptography
- Ollama / OpenAI / Anthropic / Gemini
- Pillow
- FFmpeg

## Skills demonstrated

This project demonstrates practical work with AI application architecture, LLM integration, REST APIs, Python backend engineering, browser automation, workflow orchestration, database design, credential security, scheduled jobs, analytics pipelines, and product-focused problem solving.

## Development status

SocialFlow is an actively developed portfolio project. Third-party platforms can change their APIs, authentication flows, or usage policies, so individual integrations may require maintenance. The application and tests should be run to verify the current state rather than assuming every integration is configured in every environment.

## License

MIT License.

## Author

**Akinola Ayomide Daniel**

Independent developer interested in AI, automation, software engineering, cybersecurity, digital products, and practical technology solutions.
