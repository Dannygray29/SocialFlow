# SocialFlow — AI-Powered Autonomous Social Media CMO

Self-hosted, open-source AI CMO that handles everything from news discovery to content generation, scheduling, and publishing across 12 platforms. Add your social media logins once, and AI handles the rest.

**No monthly fees. No API limits on content. Your data stays on your machine.**

## Why SocialFlow?

| Feature | SocialRails ($29-99/mo) | SocialFlow (FREE) |
|---------|------------------------|-------------------|
| Platforms | 9 | 12 (+ Discord, Reddit, Medium, Substack) |
| AI content | Capped (20-250/mo) | Unlimited (Ollama local AI) |
| Image gen | Monthly cap | GPT Image 1.5 (pay-per-use ~$0.02) |
| Content pipeline | Manual | Autonomous (AI finds, writes, posts) |
| Multi-agent | No | 6 agents (Scout, Planner, Creator, Reviewer, Publisher, Analyst) |
| Brand kit | Basic | Full (colors, logo, fonts, tone, forbidden styles) |
| Approval gates | No | Credential safety, brand voice, claim validation |
| Data ownership | Their cloud | Your machine, encrypted locally |
| Source code | Closed | Open-source |

## Quick Start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python main.py
# Dashboard at http://localhost:8000
```

## Architecture: 6-Agent Autonomous Pipeline

```
Scout → Planner → Creator → Reviewer → Publisher → Analyst
```

| Agent | Role | Schedule |
|-------|------|----------|
| **Scout** | Fetch AI news (HN, RSS), scan GitHub repos, detect trends | 8 AM, 2 PM, 8 PM |
| **Planner** | Decide what to post, which platform, what format, when | After Scout |
| **Creator** | Generate platform-specific content + branded images | After Planner |
| **Reviewer** | Quality gates: credential safety, brand voice, claims | After Creator |
| **Publisher** | Post via Playwright browser automation or API | 11 AM, 11 PM |
| **Analyst** | Track performance, generate reports, feed insights back | End of day |

## Supported Platforms (12)

| Platform | Method | Auth |
|----------|--------|------|
| LinkedIn | Playwright browser | Session persist |
| X / Twitter | Playwright browser | Session persist |
| Facebook | Playwright browser | Session persist |
| Instagram | Playwright browser | Session persist |
| Discord | Webhook (HTTP) | Webhook URL |
| Reddit | PRAW API | OAuth credentials |
| Medium | Playwright browser | Session persist |
| Substack | Playwright browser | Session persist |
| HeyGen | Playwright browser | Session persist |
| beehiiv | Playwright browser | Session persist |
| MailerLite | Playwright browser | Session persist |
| Brevo | Playwright browser | Session persist |

## AI Providers

| Provider | Cost | Setup |
|----------|------|-------|
| **Ollama** (default) | FREE | `ollama serve` + `ollama pull qwen3:8b` |
| OpenAI | Pay-per-use | Add `OPENAI_API_KEY` to `.env` |
| Anthropic | Pay-per-use | Add `ANTHROPIC_API_KEY` to `.env` |
| Google Gemini | Free tier | Add `GEMINI_API_KEY` to `.env` |

## Image Generation

Uses **GPT Image 1.5** (OpenAI's latest, replaces deprecated DALL-E 3):
- 75% cheaper than DALL-E 3 (~$0.015-0.020 per image)
- Brand-aware: auto-injects your colors, fonts, and style rules
- Platform-optimized sizes (landscape for LinkedIn/X, square for IG, portrait for stories)
- Carousel generation: 5-slide branded carousels via Pillow

## Brand Kit

Configure your brand identity from the dashboard:
- **Colors**: Primary, secondary, dark background, accents
- **Logo**: Upload once, auto-applied to carousels and watermarks
- **Typography**: Font family, heading/body weights
- **Tone**: AI content follows your voice ("clear, direct, practical")
- **Forbidden styles**: Block unwanted aesthetics in image generation
- **Hashtags**: Platform-specific hashtag presets
- **CTAs**: Reusable call-to-action templates
- **Products**: Auto-link insertion for your product URLs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Server health check |
| `/api/pipeline/run` | POST | Trigger full autonomous pipeline |
| `/api/pipeline/status` | GET | Current pipeline state |
| `/api/pipeline/queue` | GET | Content queue (drafts, approved, posted) |
| `/api/pipeline/approve/{id}` | POST | Approve a draft post |
| `/api/pipeline/reject/{id}` | POST | Reject a post |
| `/api/pipeline/publish/{id}` | POST | Publish a specific post now |
| `/api/pipeline/signals` | GET | Intelligence signals from Scout |
| `/api/pipeline/analytics` | GET | Daily/weekly performance stats |
| `/api/brand/config` | GET/PUT | Brand kit configuration |
| `/api/brand/logo` | POST | Upload brand logo |
| `/api/brand/colors` | GET | Brand color palette |
| `/api/accounts` | GET/POST | Manage platform credentials |
| `/api/posts` | GET/POST | Manage posts |
| `/api/openclaw/publish` | POST | Bridge API for external pipelines |
| `/docs` | GET | Interactive Swagger API docs |

## Security

- Credentials encrypted with **Fernet (AES-128-CBC)** — stored locally, never transmitted
- Browser sessions persisted in local `sessions/` directory
- Approval gates catch credential/PII leaks before publishing
- All actions logged with timestamps for audit trail
- No cloud dependency — everything runs on your machine

## Configuration

Copy `.env.example` to `.env` and configure:

```env
AI_PROVIDER=ollama              # ollama (free), openai, anthropic, gemini
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:8b
IMAGE_MODEL=gpt-image-1.5      # Replaces deprecated DALL-E 3
OPENAI_API_KEY=                 # Only needed for image generation
HEADLESS=false                  # true for server mode (no browser windows)
```

## Schedule (Automatic)

| Time | What Happens |
|------|-------------|
| 8:07 AM | Full pipeline: news fetch → content generation → review |
| 11:00 AM | Publish approved LinkedIn + X posts |
| 2:00 PM | Afternoon news refresh |
| 11:00 PM | Publish remaining approved posts |
| 11:30 PM | Daily analytics report |

## Tech Stack

- **Backend**: Python 3, FastAPI, SQLite, APScheduler
- **Browser Automation**: Playwright (Chromium)
- **AI**: Ollama (local), OpenAI, Anthropic, Google Gemini
- **Images**: GPT Image 1.5, Pillow (carousels)
- **Video**: FFmpeg (reels), HeyGen (avatar videos)
- **Frontend**: React (single HTML), Tailwind-inspired CSS
- **Security**: Fernet encryption, local-only credentials

## License

MIT License. Built by [InBharat AI](https://inbharat.ai).
