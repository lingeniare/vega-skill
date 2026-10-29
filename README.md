# VEGA API Studio — скилл для агента

**Русский** | [English](README.en.md)

Скилл для ИИ-ассистентов (формат `SKILL.md`) — Devin, Windsurf, Claude Code и других инструментов, которые читают agent skills. Учит агента работать с **VEGA API** (`api.vega.chat`) — полностью совместимым прокси OpenRouter.

Суть простая: меняешь `https://openrouter.ai/api/v1` на `https://api.vega.chat/api/v1`, пути эндпоинтов остаются теми же, ключ — от VEGA. Вся документация OpenRouter применима как есть.

## Что умеет скилл

| Сценарий | Что делает |
|---|---|
| **A — Создать приложение** | Собирает новые приложения/сервисы на VEGA через официальный OpenAI SDK с кастомным `base_url` |
| **B — Подключить приложение** | Переводит существующий код с OpenRouter/OpenAI на VEGA заменой base URL и ключа |
| **C — Генерировать медиа** | Картинки, видео, озвучка (TTS), транскрипция (STT) и музыка через `scripts/vega.py` |
| **Цены** | `GET /pricing` — цены моделей в рублях и долларах с наценкой VEGA |

Плюс: поиск моделей, настройка `.env`, особенности стриминга, лимиты и обработка ошибок — всё проверено на живом API.

## Структура репозитория

```
vega-api-studio/
├── SKILL.md                  # Манифест скилла и сценарии работы
├── references/
│   ├── integration.md        # Примеры для SDK: .env, Python, TypeScript/Next.js, ошибки
│   └── media.md              # Медиа-эндпоинты, проверенные на живом API
└── scripts/
    └── vega.py               # CLI для генерации медиа — Python 3, только стандартная библиотека
```

## Быстрый старт

Возьми ключ на https://api.vega.chat/dashboard, затем:

```bash
export VEGA_API_KEY=sk-...   # Windows PowerShell: $env:VEGA_API_KEY="sk-..."

cd vega-api-studio
python scripts/vega.py models --output image     # список моделей картинок (ключ не нужен)
python scripts/vega.py image "Рыжая панда-астронавт в открытом космосе" \
    -m openai/gpt-image-2.5-sunburst --aspect 3:2 -o panda.png
python scripts/vega.py speech "Привет, мир" -m <модель> -o voice.mp3
python scripts/vega.py transcribe voice.mp3 -m <модель> --language ru
python scripts/vega.py music "Спокойное lo-fi пианино, 80 bpm" -m google/lyria-3-clip-preview -o music.mp3
python scripts/vega.py video "Съёмка с дрона над морем на закате" -m <модель>
```

Видео генерируется асинхронно — скрипт сам опрашивает задачу и скачивает готовый mp4.

## Установка как скилл

Скопируй папку `vega-api-studio/` в директорию скиллов агента:

- `~/.agents/skills/` — на уровне пользователя (работает во всех проектах)
- `<проект>/.agents/skills/` или `<проект>/.devin/skills/` — на уровне проекта

Дальше агент подхватит его сам, когда попросишь что-то вроде «сделай картинку», «озвучь текст», «сгенерируй видео» или «подключи api.vega.chat».

## Документация

- Ключи и баланс: https://api.vega.chat/dashboard
- Документация OpenRouter (те же эндпоинты): https://openrouter.ai/docs
- Справочник VEGA для LLM: https://api.vega.chat/llms.txt

## Важные нюансы

- Никогда не свети `VEGA_API_KEY` в браузере — вызывай VEGA только с бэкенда или route handler'а.
- `polling_url` из ответа `POST /videos` ведёт на `openrouter.ai`. Игнорируй его и опрашивай `GET /videos/{id}` на VEGA; ключ нельзя отправлять на `polling_url` и `unsigned_urls`.
- `/credits` и `/openapi.json` на VEGA отдают 404 — для лимитов и баланса используй `GET /key`, для документации — `llms.txt`.

## Требования

- Python 3 (только стандартная библиотека — для `vega.py` ничего ставить не нужно)
- `VEGA_API_KEY` для генерации; списки моделей работают без ключа
