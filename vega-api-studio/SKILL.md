---
name: vega-api-studio
description: Build apps with the VEGA API (api.vega.chat, a 100% OpenRouter proxy), connect existing apps to it, and generate images, video, speech, transcripts and other media through it. Use this skill whenever the user wants to create an app or service on top of VEGA/OpenRouter, switch an existing app, SDK or tool to the VEGA base URL, or generate pictures, video, voice-over, TTS, STT, audio or "music" from a prompt, even if they only say "сделай картинку", "озвучь текст", "сгенерируй видео", "подключи к API" or "api.vega.chat". Also use it for model discovery, API keys, .env setup and error debugging with VEGA.
---

# VEGA API Studio

VEGA proxies OpenRouter. For API requests, replace `https://openrouter.ai/api/v1` with `https://api.vega.chat/api/v1`, preserving the endpoint path and query parameters. Use a VEGA API key. Documentation links remain unchanged.

- Base URL: `https://api.vega.chat/api/v1`
- Auth: `Authorization: Bearer $VEGA_API_KEY` (keys: https://api.vega.chat/dashboard)
- OpenRouter docs: https://openrouter.ai/docs
- OpenRouter docs on Context7: https://context7.com/websites/openrouter_ai/llms.txt?tokens=100000
- Models are `author/name`, e.g. `openai/gpt-6.1-terra`. Never hardcode a model from memory for media: list them first.

Related skill `api-vega-chat` has a per-endpoint reference for text endpoints. For media, trust `references/media.md` here: it was checked against the live API.

## Pick the workflow

| User wants | Do this |
|---|---|
| New app / service using LLMs | Workflow A |
| Connect an existing app, SDK or tool | Workflow B |
| Image, video, speech, transcript, audio | Workflow C |
| Current model prices / cost estimate | `GET /pricing` (see "Model prices") |

Always start by stating a short plan and acceptance criteria (the user's rule), and end by checking each criterion. Reply in Russian, in plain language.

## Workflow A: create an app

1. Clarify: language/framework, which feature (chat, image, voice, video), where the key lives.
2. Use the official OpenAI SDK with `baseURL`/`base_url` set to VEGA. No custom client needed. Snippets: `references/integration.md`.
3. Put the key in `.env` as `VEGA_API_KEY`, add `.env` to `.gitignore`, never expose it to the browser. Call VEGA from a server route or backend.
4. Add error handling and streaming where it helps UX (see `references/integration.md`).
5. Run the app or a smoke test (`scripts/vega.py models`) before claiming it works.

## Workflow B: connect an app to VEGA

1. Find where the base URL is set (`grep` for `openrouter.ai`, `api.openai.com`, `OPENAI_BASE_URL`).
2. Change only base URL + key variable. Keep model ids in `author/name` form.
3. Optional headers: `HTTP-Referer`, `X-Title`.
4. Verify with one real request. Tool-specific env vars: `references/integration.md`.

## Workflow C: generate media

Use `scripts/vega.py` (Python 3, standard library only) for quick results, or copy its logic into the user's app.

```
python scripts/vega.py models [--output image|video|audio|speech|transcription|embeddings|text]   # no key needed
python scripts/vega.py image  "prompt" -m <model> [-o out.png] [--aspect 16:9 --resolution 1K --quality high --format png -n 1 --ref URL --seed N --via-chat]
python scripts/vega.py speech "text"   -m <model> [--voice V --speed 1.0 --format mp3] [-o out.mp3]
python scripts/vega.py transcribe file.mp3 -m <model> [--language ru]
python scripts/vega.py music  "prompt" -m google/lyria-3-clip-preview [-o music.mp3]
python scripts/vega.py video  "prompt" -m <model> [--duration 5 --resolution 720p --aspect 16:9 --audio off --first-frame URL --last-frame URL --ref URL --seed N]
```

Steps:
1. Run `models --output <kind>` to find model ids. For image options, check `GET /images/models/{author}/{model}/endpoints`; the script lists ids only. Video listings also show durations, resolutions, aspect ratios and frame support.
2. Confirm the user accepts the cost before generating paid media (current rates: `GET /pricing`). Choose an unused output path: the script overwrites existing files. Video is asynchronous: the script polls until done and downloads the file.
3. Tell the user the output path.

GPT image example (run from the skill directory with `VEGA_API_KEY` set):

```bash
python scripts/vega.py image "A red panda astronaut floating in space, studio lighting" -m openai/gpt-image-2.5-sunburst --aspect 3:2 --quality high --format png -o panda.png
```

This uses `POST /images` and saves the decoded `data[].b64_json`. Check the model's current availability and endpoint parameters first; do not assume `--resolution` is supported by this model.

Endpoint details, request bodies and caveats: `references/media.md`.

## Model prices

`GET /pricing` with the usual `Authorization: Bearer $VEGA_API_KEY` returns per-model prices with the VEGA markup, in RUB and USD. Same formulas as the dashboard: RUB = OpenRouter price × markup × FX rate, USD = OpenRouter price × markup.

Fields per model: `prompt_rub_per_1m`, `completion_rub_per_1m`, `image_rub_per_1m`, `input_cache_read_rub_per_1m`, `input_cache_write_rub_per_1m` (null when the model has no cache pricing), `request_rub`, `image_rub`, and the USD twins `prompt_usd_per_1m`, `completion_usd_per_1m`, `image_usd_per_1m`, `input_cache_read_usd_per_1m`, `input_cache_write_usd_per_1m`, `request_usd`, `image_usd`.

Query params: `?search=` (name search), `?model=` (exact model), `?limit=&page=` (pagination). Visibility rules match `/models`: officevega keys are limited to the whitelist. Full details and a response example: VEGA API Reference, "Цены моделей в рублях и долларах".

## Gotchas

- Images: `POST /images` returns `data[].b64_json`. Only text+image models can also use `/chat/completions` with `modalities`.
- TTS is `POST /audio/speech` (raw bytes, default is pcm, some models accept only pcm or need an explicit `voice`). STT is `POST /audio/transcriptions` with base64 `input_audio`; some models need multipart (script falls back automatically). `/transcriptions` is 404.
- Music = Lyria via `/chat/completions` with `modalities: ["text","audio"]` and `stream: true`. Verified live.
- Video `polling_url` points to openrouter.ai: poll `/videos/{id}` on VEGA yourself. Never send the key to `polling_url` or `unsigned_urls`; download via `/videos/{id}/content`.
- Streams contain `:` comment lines. Skip them before `JSON.parse`.
- Rate limits are per account. `GET /key` shows limits and balance (`/credits` is 404 on VEGA).
- There is no `/openapi.json` on VEGA.
