# VEGA API Studio — Agent Skill

**English** | [Русский](README.ru.md)

An agent skill (`SKILL.md` format) that teaches AI coding assistants — Devin, Windsurf, Claude Code and any tool that reads agent skills — how to work with the **VEGA API** (`api.vega.chat`), a 100% OpenRouter-compatible proxy.

The core idea: replace `https://openrouter.ai/api/v1` with `https://api.vega.chat/api/v1`, keep the endpoint paths, and use a VEGA API key. All OpenRouter documentation applies as-is.

## What the skill covers

| Workflow | Purpose |
|---|---|
| **A — Create an app** | Scaffold new apps/services on VEGA using the official OpenAI SDK with a custom `base_url` |
| **B — Connect an app** | Migrate existing OpenRouter/OpenAI code to VEGA by swapping base URL + key |
| **C — Generate media** | Images, video, speech (TTS), transcription (STT) and music via `scripts/vega.py` |
| **Pricing** | `GET /pricing` — per-model prices in RUB and USD with the VEGA markup |

Also covers model discovery, `.env` setup, streaming quirks, rate limits and error handling — all verified against the live API.

## Repository layout

```
vega-api-studio/
├── SKILL.md                  # Skill manifest and workflows
├── references/
│   ├── integration.md        # SDK snippets: .env, Python, TypeScript/Next.js, errors
│   └── media.md              # Media endpoints verified against the live API
└── scripts/
    └── vega.py               # Media CLI — Python 3, standard library only
```

## Quick start

Get a key at https://api.vega.chat/dashboard, then:

```bash
export VEGA_API_KEY=sk-...   # Windows PowerShell: $env:VEGA_API_KEY="sk-..."

cd vega-api-studio
python scripts/vega.py models --output image     # list image models (no key needed)
python scripts/vega.py image "A red panda astronaut floating in space" \
    -m openai/gpt-image-2.5-sunburst --aspect 3:2 -o panda.png
python scripts/vega.py speech "Hello world" -m <model> -o voice.mp3
python scripts/vega.py transcribe voice.mp3 -m <model> --language ru
python scripts/vega.py music "Calm lo-fi piano, 80 bpm" -m google/lyria-3-clip-preview -o music.mp3
python scripts/vega.py video "A drone shot over the sea at sunset" -m <model>
```

Video is asynchronous — the script polls the job and downloads the mp4 automatically.

## Install as a skill

Copy the `vega-api-studio/` folder into your agent's skills directory:

- `~/.agents/skills/` — user-level (works across projects)
- `<project>/.agents/skills/` or `<project>/.devin/skills/` — project-level

After that the agent picks it up automatically when you ask for things like "сделай картинку", "озвучь текст", "сгенерируй видео" or "подключи api.vega.chat".

## Documentation

- API keys and balance: https://api.vega.chat/dashboard
- OpenRouter docs (same endpoints): https://openrouter.ai/docs
- VEGA reference for LLMs: https://api.vega.chat/llms.txt

## Caveats worth knowing

- Never expose `VEGA_API_KEY` to the browser — call VEGA only from a backend or route handler.
- The `polling_url` returned by `POST /videos` points to `openrouter.ai`. Ignore it and poll `GET /videos/{id}` on VEGA instead; never send your key to `polling_url` or `unsigned_urls`.
- `/credits` and `/openapi.json` are 404 on VEGA — use `GET /key` for limits/balance and `llms.txt` for docs.

## Requirements

- Python 3 (standard library only — no `pip install` needed for `vega.py`)
- `VEGA_API_KEY` for generation endpoints; model listings work without a key
