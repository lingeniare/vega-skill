# Integrating apps with VEGA

## .env

```
VEGA_API_KEY=sk-...
VEGA_BASE_URL=https://api.vega.chat/api/v1
```

## Python

```python
import os
from openai import OpenAI
client = OpenAI(base_url=os.environ["VEGA_BASE_URL"], api_key=os.environ["VEGA_API_KEY"])
r = client.chat.completions.create(model="openai/gpt-4o", messages=[{"role": "user", "content": "Hi"}])
print(r.choices[0].message.content)
```

## TypeScript / Next.js (server only)

```ts
import OpenAI from "openai";
export const vega = new OpenAI({
  baseURL: process.env.VEGA_BASE_URL,
  apiKey: process.env.VEGA_API_KEY,
  defaultHeaders: { "HTTP-Referer": "https://yourapp.com", "X-Title": "Your App" },
});
```

Use it in a Route Handler (`app/api/.../route.ts`), never in client components. Install with `pnpm add openai`.

## Streaming (fetch)

Send `stream: true`, read lines starting with `data: `, skip lines starting with `:`, stop at `data: [DONE]`.

## Existing tools

| Tool | Setting |
|---|---|
| OpenAI SDKs / most clients | `OPENAI_BASE_URL=https://api.vega.chat/api/v1`, `OPENAI_API_KEY=<vega key>` |
| LangChain / LlamaIndex | `base_url` / `api_base` of the OpenAI class |
| Anthropic-style clients | `POST /messages` is supported, point base URL to `https://api.vega.chat/api` |
| Raw OpenRouter code | replace `https://openrouter.ai/api/v1` with the VEGA base URL |

## Errors

- 401: bad or missing key. 402: no credits (check `GET /key`). 429: rate limit, retry with exponential backoff. 5xx: retry a few times.
- Error body: `{"error": {"code": ..., "message": ...}}`. Show `message` to the user.
- During streaming, errors can arrive as an SSE event after a 200 status. Check each chunk for an `error` field.

