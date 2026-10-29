# Media generation via VEGA

Verified with a real key on 2026-10-29 (image, speech, transcription, music, video all ran end to end) and against the live api.vega.chat docs (`https://api.vega.chat/llms.txt`, page URL + `.md`) and live model lists. Base: `https://api.vega.chat/api/v1`. There is no `/openapi.json`; use `llms.txt` and `/docs/api-reference/.../*.md` instead.

## Discover models (public, no key)

```
GET /models?output_modalities=image|video|audio|speech|transcription|embeddings|text
GET /videos/models     # durations, resolutions, aspect ratios, frame support
GET /images/models     # image models and their supported_parameters
GET /images/models/{author}/{model}/endpoints  # per-provider supported_parameters
```

Live counts when checked: ~60 image, 30 video, 38 speech (TTS), 28 transcription, 4 audio-out.
Always pick the model from these lists; ids change often. `vega.py models --output image` prints ids only, so inspect the image endpoints separately for supported options.

## Images: `POST /images`

```json
{"model": "<image model>", "prompt": "...", "aspect_ratio": "16:9", "resolution": "2K",
 "quality": "high", "output_format": "png", "n": 1, "seed": 1,
 "input_references": [{"type": "image_url", "image_url": {"url": "https://... or data:..."}}]}
```

Response: `{"created", "data": [{"b64_json", "media_type"}], "usage": {"cost"}}`. Decode `b64_json`; `media_type` is present when the format is identifiable. `svg` output is base64 of UTF-8 markup. Max 16 references, `n` 1-10 but many models allow only 1. Check each provider's limits in `/images/models/{author}/{model}/endpoints`.

The optional `size` is a resolution tier such as `2K` or pixel dimensions such as `2048x2048`, not an aspect ratio; `vega.py` does not expose it. `n` is an upper bound, and providers may return fewer images.

For example, `openai/gpt-image-2.5-sunburst` listed `aspect_ratio`, `quality`, `n` and `input_references` when checked on 2026-10-29, but not `resolution`; its listed quality values included `xhigh` and `max`. See the GPT command in `SKILL.md`; recheck the endpoint before use because supported options can change.

Models with `text+image` output (e.g. `google/gemini-nano-banana-2.1`) can also work through `/chat/completions` with `"modalities": ["image","text"]`; images come back as `message.images[].image_url.url` data URLs (`vega.py image --via-chat`).

## Speech (TTS): `POST /audio/speech` -> raw audio bytes

```json
{"model": "elevenlabs/eleven-v4-turbo", "input": "Привет!", "voice": "<provider voice id>", "response_format": "mp3", "speed": 1}
```

`response_format`: `mp3` or `pcm` (default `pcm`). Support differs per model: `fish-audio/s2.1-pro-free:free` returned mp3 fine, `heygen/heygen-voice-1-turbo:free` accepts only `pcm` (HTTP 400 otherwise). `voice` is provider specific and some models require it explicitly (`hexgrad/kokoro-82m` returns 400 without one). On a 400, read the error message and adjust. Voice cloning: `input_references` with an `input_audio` part (data URL) plus optional `text` transcript, only for models that support cloning.

## Transcription (STT): `POST /audio/transcriptions` (JSON or multipart)

```json
{"model": "elevenlabs/scribe-v2", "input_audio": {"data": "<base64>", "format": "mp3"}, "language": "ru"}
```

Response `{"text", "usage"}`. Some models (e.g. `mistralai/voxtral-mini-transcribe-3-0`) reject JSON with "Failed to parse request body as FormData": send `multipart/form-data` (`file`, `model`, `language`; max 25 MB) instead. `vega.py transcribe` does this fallback automatically. `elevenlabs/scribe-v2` works with JSON. `response_format: "verbose_json"` (+ `timestamp_granularities`) works only on OpenAI-compatible providers. Note: `/transcriptions` (without `/audio`) returns 404.

## Video: async job

1. `POST /videos`
```json
{"model": "<video model>", "prompt": "...", "duration": 5, "resolution": "720p", "aspect_ratio": "16:9",
 "generate_audio": false, "seed": 1,
 "frame_images": [{"type": "image_url", "image_url": {"url": "..."}, "frame_type": "first_frame"}],
 "input_references": [{"type": "image_url", "image_url": {"url": "..."}}],
 "callback_url": "https://..."}
```
Only `model` is required (prompt is optional for image-only models). Allowed durations/resolutions/frames per model are in `/videos/models` (e.g. `last_frame` only where listed). `size` ("1280x720") is an alternative to resolution + aspect_ratio.

2. Response: `{"id", "polling_url", "status"}`. WARNING: `polling_url` points to `https://openrouter.ai/api/v1/videos/...`, not VEGA. Ignore it and poll `GET https://api.vega.chat/api/v1/videos/{id}` with your key every ~10 s (a 3 s 480p clip finished in about 30 s). Statuses: `pending`, `in_progress`, `completed`, `failed`, `cancelled`, `expired`. A failed job has `error`.
3. Download `GET /videos/{id}/content?index=0` (mp4 bytes, send the bearer header). `unsigned_urls` also appear on completion, but do not send your API key to those third-party URLs.
4. `callback_url` (HTTPS) gives a signed webhook instead of polling.

## Music: Lyria through chat completions

Models with audio output (`/models?output_modalities=audio`): `google/lyria-3-clip-preview` (30 s clip, about $0.04), `google/lyria-3-pro-preview` (full song, about $0.08), plus `openai/gpt-audio(-mini)` for spoken audio.

```json
{"model": "google/lyria-3-clip-preview", "messages": [{"role": "user", "content": "Calm lo-fi piano, 80 bpm"}],
 "modalities": ["text", "audio"], "stream": true}
```

Audio arrives as base64 chunks in `choices[].delta.audio.data`; concatenate and decode (`vega.py music`). Verified: with `google/lyria-3-clip-preview` the stream returns audio chunks that decode to an MP3 (ID3 header, about 740 KB). Instrumental prompts return the text `<instrumental>` along with the audio.

## Other

`POST /rerank`, `POST /embeddings` (`GET /embeddings/models`), `POST /responses`, `POST /messages` (Anthropic), `GET /key` (limits and balance; `/credits` returns 404 on VEGA).
