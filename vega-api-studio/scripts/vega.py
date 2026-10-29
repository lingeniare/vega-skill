#!/usr/bin/env python3
"""VEGA API media CLI (stdlib only). Needs VEGA_API_KEY. Base URL override: VEGA_BASE_URL."""
import argparse, base64, json, os, sys, time, urllib.error, urllib.parse, urllib.request

BASE = os.environ.get("VEGA_BASE_URL", "https://api.vega.chat/api/v1").rstrip("/")
ORIGIN = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(BASE))


class ApiError(Exception):
    pass


def _open(method, path, body=None, multipart=None):
    key = os.environ.get("VEGA_API_KEY")
    if not key and not path.startswith("/models") and not path.startswith("/videos/models"):
        sys.exit("Set VEGA_API_KEY first (https://api.vega.chat/dashboard).")
    url = path if path.startswith("http") else (ORIGIN + path if path.startswith("/api/") else BASE + path)
    headers = {"X-Title": "vega-api-studio"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if multipart:
        fn, model, lang = multipart
        bd = "----vega" + str(int(time.time() * 1000))
        parts = [(k, v) for k, v in (("model", model), ("language", lang)) if v]
        data = b"".join(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in parts)
        data += (f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(fn)}"\r\n\r\n'.encode()
                 + open(fn, "rb").read() + f"\r\n--{bd}--\r\n".encode())
        headers["Content-Type"] = f"multipart/form-data; boundary={bd}"
    try:
        return urllib.request.urlopen(urllib.request.Request(url, data, headers, method=method), timeout=600)
    except urllib.error.HTTPError as e:
        raise ApiError(f"HTTP {e.code}: {e.read().decode(errors='replace')}")


def req(method, path, body=None, raw=False, multipart=None):
    with _open(method, path, body, multipart) as r:
        content = r.read()
    return content if raw else json.loads(content)


def save(path, content):
    with open(path, "wb") as f:
        f.write(content)
    print(f"Saved: {os.path.abspath(path)}")


def numbered(path, i):
    base, ext = os.path.splitext(path)
    return path if i == 0 else f"{base}_{i}{ext}"


def cmd_models(a):
    if a.output == "video":
        for m in req("GET", "/videos/models")["data"]:
            print(f"{m['id']}  durations={m.get('supported_durations')} res={m.get('supported_resolutions')} "
                  f"aspect={m.get('supported_aspect_ratios')} frames={m.get('supported_frame_images')}")
        return
    for m in req("GET", "/models" + (f"?output_modalities={a.output}" if a.output else ""))["data"]:
        print(m["id"])


def cmd_image(a):
    if a.via_chat:
        body = {"model": a.model, "messages": [{"role": "user", "content": a.prompt}], "modalities": ["image", "text"]}
        if a.aspect:
            body["image_config"] = {"aspect_ratio": a.aspect}
        msg = req("POST", "/chat/completions", body)["choices"][0]["message"]
        urls = [i["image_url"]["url"] for i in msg.get("images") or []]
        if not urls:
            sys.exit(f"No image returned. Model said: {msg.get('content')}")
        for i, u in enumerate(urls):
            save(numbered(a.output, i), base64.b64decode(u.split(",", 1)[1]))
        return
    body = {"model": a.model, "prompt": a.prompt}
    for k, v in (("aspect_ratio", a.aspect), ("resolution", a.resolution), ("quality", a.quality),
                 ("output_format", a.format), ("n", a.n), ("seed", a.seed)):
        if v is not None:
            body[k] = v
    if a.ref:
        body["input_references"] = [{"type": "image_url", "image_url": {"url": u}} for u in a.ref]
    items = req("POST", "/images", body)["data"]
    for i, it in enumerate(items):
        save(numbered(a.output, i), base64.b64decode(it["b64_json"]))


def cmd_speech(a):
    body = {"model": a.model, "input": a.text, "response_format": a.format}
    if a.voice:
        body["voice"] = a.voice
    if a.speed:
        body["speed"] = a.speed
    save(a.output or f"speech.{a.format}", req("POST", "/audio/speech", body, raw=True))


def cmd_transcribe(a):
    fmt = a.format or os.path.splitext(a.file)[1].lstrip(".").lower() or "mp3"
    with open(a.file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    body = {"model": a.model, "input_audio": {"data": data, "format": fmt}}
    if a.language:
        body["language"] = a.language
    try:
        print(req("POST", "/audio/transcriptions", body).get("text", ""))
    except ApiError as e:
        if "FormData" not in str(e):
            raise
        print(req("POST", "/audio/transcriptions", multipart=(a.file, a.model, a.language)).get("text", ""))


def cmd_music(a):
    body = {"model": a.model, "messages": [{"role": "user", "content": a.prompt}],
            "modalities": ["text", "audio"], "stream": True}
    chunks, text = [], []
    with _open("POST", "/chat/completions", body) as r:
        for line in r:
            line = line.decode("utf-8", "replace").strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            ev = json.loads(line[5:])
            if ev.get("error"):
                sys.exit(f"Error: {ev['error']}")
            for ch in ev.get("choices", []):
                d = ch.get("delta") or ch.get("message") or {}
                au = d.get("audio") or {}
                if au.get("data"):
                    chunks.append(au["data"])
                if d.get("content"):
                    text.append(d["content"])
    if not chunks:
        sys.exit("No audio returned. Text: " + "".join(text)[:500])
    if text:
        print("".join(text).strip())
    save(a.output, base64.b64decode("".join(chunks)))


def cmd_video(a):
    body = {"model": a.model}
    if a.prompt:
        body["prompt"] = a.prompt
    for k, v in (("duration", a.duration), ("resolution", a.resolution), ("aspect_ratio", a.aspect), ("seed", a.seed)):
        if v is not None:
            body[k] = v
    if a.audio is not None:
        body["generate_audio"] = a.audio == "on"
    frames = [{"type": "image_url", "image_url": {"url": u}, "frame_type": t}
              for t, u in (("first_frame", a.first_frame), ("last_frame", a.last_frame)) if u]
    if frames:
        body["frame_images"] = frames
    if a.ref:
        body["input_references"] = [{"type": "image_url", "image_url": {"url": u}} for u in a.ref]
    job = req("POST", "/videos", body)
    print(f"Job {job['id']} started, polling every 10s...")
    while job.get("status") in ("pending", "in_progress"):
        time.sleep(10)
        job = req("GET", f"/videos/{job['id']}")
        print(f"  status: {job.get('status')}")
    if job["status"] != "completed":
        sys.exit(f"Video {job['status']}: {job.get('error') or json.dumps(job)}")
    save(a.output, req("GET", f"/videos/{job['id']}/content?index=0", raw=True))
    if job.get("usage"):
        print(f"Cost: {job['usage'].get('cost')}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="cmd", required=True)

    c = s.add_parser("models", help="list models (no key needed)")
    c.add_argument("--output", choices=["image", "video", "audio", "speech", "transcription", "embeddings", "text"])
    c.set_defaults(f=cmd_models)

    c = s.add_parser("image"); c.add_argument("prompt"); c.add_argument("-m", "--model", required=True)
    c.add_argument("-o", "--output", default="image.png"); c.add_argument("--aspect"); c.add_argument("--resolution")
    c.add_argument("--quality"); c.add_argument("--format", choices=["png", "jpeg", "webp", "svg"])
    c.add_argument("-n", type=int); c.add_argument("--seed", type=int)
    c.add_argument("--ref", action="append", help="reference image URL or data URL (repeatable)")
    c.add_argument("--via-chat", action="store_true", help="use /chat/completions for text+image models")
    c.set_defaults(f=cmd_image)

    c = s.add_parser("speech"); c.add_argument("text"); c.add_argument("-m", "--model", required=True)
    c.add_argument("--voice"); c.add_argument("--speed", type=float); c.add_argument("--format", default="mp3", choices=["mp3", "pcm"])
    c.add_argument("-o", "--output"); c.set_defaults(f=cmd_speech)

    c = s.add_parser("transcribe"); c.add_argument("file"); c.add_argument("-m", "--model", required=True)
    c.add_argument("--language"); c.add_argument("--format"); c.set_defaults(f=cmd_transcribe)

    c = s.add_parser("music", help="e.g. google/lyria-3-clip-preview"); c.add_argument("prompt")
    c.add_argument("-m", "--model", required=True); c.add_argument("-o", "--output", default="music.mp3"); c.set_defaults(f=cmd_music)

    c = s.add_parser("video"); c.add_argument("prompt", nargs="?"); c.add_argument("-m", "--model", required=True)
    c.add_argument("--duration", type=int); c.add_argument("--resolution"); c.add_argument("--aspect"); c.add_argument("--seed", type=int)
    c.add_argument("--audio", choices=["on", "off"]); c.add_argument("--first-frame"); c.add_argument("--last-frame")
    c.add_argument("--ref", action="append", help="reference image URL (repeatable)")
    c.add_argument("-o", "--output", default="video.mp4"); c.set_defaults(f=cmd_video)

    a = p.parse_args()
    try:
        a.f(a)
    except ApiError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()

