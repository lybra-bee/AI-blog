#!/usr/bin/env python3
# coding: utf-8
"""
content_generator.py
Генерирует статьи и (по возможности) изображение для каждой статьи.
Исправления:
 - Проверка наличия OPENROUTER_API_KEY
 - Обработка ошибок и повторные попытки при запросах
 - Санитизация имён файлов
 - Не ломает процесс, если генерация изображения не доступна
 - Создаёт корректный Markdown-файл в content/posts
"""

import os
import re
import time
import json
import random
from datetime import datetime
from pathlib import Path

try:
    import requests
except Exception:
    raise SystemExit("Требуется библиотека requests. Установите: pip install requests")

# --- Настройка путей и промптов ---
POSTS_DIR = Path("content/posts")
IMG_DIR = Path("static/images/gallery")
PROMPTS = [
    "Обзор новой архитектуры нейросети",
    "Урок по использованию Python для ИИ",
    "Мастер-класс: генерация изображений нейросетями",
    "Будущее высоких технологий",
    "Нейросети в медицине",
    "ИИ и кибербезопасность",
    "Как работает обучение с подкреплением",
    "Тенденции машинного обучения 2025",
]

IMAGE_PROMPTS = [
    "futuristic neural network visualization, neon cyberpunk style, high tech background",
    "abstract AI brain, glowing circuits, futuristic background",
    "digital neural network, colorful, high resolution background"
]

# --- Утилиты ---
def slugify(name: str) -> str:
    """Санитизация названия в пригодный для имени файла slug."""
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)         # удалить неалфанумерические символы
    s = re.sub(r"[\s_]+", "-", s)          # пробелы и подчеркивания в -
    s = s.strip("-")
    return s[:200]                         # ограничение длины

def get_api_key() -> str | None:
    """Получить ключ из окружения."""
    return os.getenv("OPENROUTER_API_KEY")

# --- HTTP helpers с ретраями ---
def post_with_retries(url, headers=None, json_payload=None, max_retries=3, backoff=1.0, timeout=30):
    """POST-запрос с простыми повторами и обработкой ошибок."""
    attempt = 0
    while attempt < max_retries:
        try:
            r = requests.post(url, headers=headers, json=json_payload, timeout=timeout)
            return r
        except requests.RequestException as e:
            attempt += 1
            wait = backoff * attempt
            print(f"[WARN] Ошибка запроса ({e}), попытка {attempt}/{max_retries}, ждём {wait}s")
            time.sleep(wait)
    return None

# --- Генерация текста статьи ---
def generate_text(title: str) -> str:
    key = get_api_key()
    if not key:
        print("[WARN] OPENROUTER_API_KEY не задан. Возвращаю заглушку.")
        return f"# {title}\n\n(Автогенерация выключена — отсутствует API-ключ.)\n"

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"Ты пишешь статьи для блога про ИИ и технологии. Стиль — обзор, урок или мастер-класс."},
            {"role":"user","content":f"Напиши развернутую статью на тему: {title}. Формат: заголовок, короткое введение, 3-5 разделов с подзаголовками, заключение. Включи краткую аннотацию (summary)."}
        ],
        "max_tokens": 1200
    }

    r = post_with_retries(url, headers=headers, json_payload=data, max_retries=3, backoff=2.0)
    if r is None:
        print("[ERROR] Не удалось достучаться до OpenRouter API после попыток.")
        return f"# {title}\n\n(Ошибка генерации — API недоступен.)\n"

    if r.status_code != 200:
        print(f"[ERROR] API вернул {r.status_code}: {r.text}")
        return f"# {title}\n\n(Ошибка генерации — код {r.status_code}.)\n"

    try:
        payload = r.json()
        # подстраховка по структуре ответа
        content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            print("[WARN] Ответ API не содержит ожидаемого поля content.")
            return f"# {title}\n\n(Пустой ответ API.)\n"
        return content
    except Exception as e:
        print(f"[ERROR] Ошибка разбора JSON: {e}")
        return f"# {title}\n\n(Ошибка разбора ответа API.)\n"

# --- Генерация (или скачивание) изображения ---
def generate_image(prompt: str, out_path: Path) -> bool:
    """
    Ставит попытку получить изображение по prompt.
    В продакшене вы можете подключить свой генератор (StableDiffusion, DALL·E и т.п.)
    Здесь — пробная попытка через сервис Pollinations (GET), если не доступен — вернуть False.
    """
    # ВНИМАНИЕ: внешний сервис может менять API. Этот код — best-effort заглушка.
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ','%20')}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and r.content:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(r.content)
            return True
        print(f"[WARN] Генерация изображения вернула {r.status_code}")
    except requests.RequestException as e:
        print(f"[WARN] Ошибка при загрузке изображения: {e}")
    return False

# --- Сохранение поста на диск ---
def save_post(title: str, body: str, featured_image_filename: str | None = None) -> Path:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = POSTS_DIR / f"{today}-{slug}.md"
    frontmatter = [
        "+++",
        f'title = "{title.replace(\'"\', "\'")}"',
        'draft = false',
    ]
    if featured_image_filename:
        frontmatter.append(f'featured_image = "{featured_image_filename}"')
    frontmatter.append("+++")
    content = "\n".join(frontmatter) + "\n\n" + body.strip() + "\n"
    filename.write_text(content, encoding="utf-8")
    print(f"[INFO] Пост сохранён: {filename}")
    return filename

# --- Main ---
def main():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    title = random.choice(PROMPTS)
    print(f"[INFO] Генерируем статью: {title}")

    content = generate_text(title)

    # пробуем сгенерировать изображение
    image_prompt = random.choice(IMAGE_PROMPTS)
    img_slug = slugify(title)
    img_filename = f"{datetime.now().strftime('%Y-%m-%d')}-{img_slug}.png"
    img_path = IMG_DIR / img_filename

    image_ok = generate_image(image_prompt, img_path)
    if image_ok:
        print(f"[INFO] Изображение сгенерировано: {img_path}")
        featured = f"gallery/{img_filename}"
    else:
        print("[WARN] Не удалось сгенерировать изображение, оставляю без featured_image.")
        featured = None

    save_post(title, content, featured_image_filename=featured)
    print("[INFO] Готово.")

if __name__ == "__main__":
    main()
