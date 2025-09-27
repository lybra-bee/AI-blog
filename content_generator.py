#!/usr/bin/env python3
# coding: utf-8
"""
Robust content generator for AI-blog.
- Writes posts to content/posts
- Saves images to static/images/gallery
- Uses OpenRouter if OPENROUTER_API_KEY is set; otherwise creates a safe fallback article
"""

import os
import re
import time
import json
import random
import requests
from datetime import datetime
from pathlib import Path

# --- Config ---
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
    "abstract AI circuit board, neon, high detail",
]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Helpers ---
def slugify(text: str, maxlen: int = 60) -> str:
    text = text.lower()
    # replace cyrillic and spaces by hyphen safe approach: remove anything not alnum or dash, then collapse dashes
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9\-а-яё]', '-', text)
    text = re.sub(r'-{2,}', '-', text)
    text = text.strip('-')
    return text[:maxlen]

def ensure_dirs():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

def download_random_image(dest: Path, width=1200, height=630):
    # Uses picsum.photos for a simple random image (no API key)
    url = f"https://picsum.photos/{width}/{height}"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print("Warning: failed to download random image:", e)
        return False

def pick_existing_image() -> Path:
    imgs = [p for p in IMG_DIR.iterdir() if p.is_file()]
    return random.choice(imgs) if imgs else None

# --- OpenRouter interaction (robust) ---
def generate_text_via_openrouter(title: str, attempts=3, timeout=15):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"Ты пишешь статьи для блога про ИИ и технологии. Стиль — обзор, урок или мастер-класс."},
            {"role":"user","content":f"Напиши подробную статью на тему: {title}. Структура: заголовок, вводный абзац, несколько секций с подзаголовками и заключение. Объем ~500-800 слов."}
        ],
        "max_tokens": 1200
    }
    for i in range(attempts):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            data = r.json()
            if r.status_code == 200 and "choices" in data and data["choices"]:
                # model might return message structure
                message = data["choices"][0].get("message")
                if isinstance(message, dict):
                    return message.get("content", "").strip()
                # fallback to 'text' or similar
                return data["choices"][0].get("text", "").strip()
            else:
                # print server message for debugging
                print("OpenRouter response:", json.dumps(data, ensure_ascii=False))
                # if 402 or other code, break
                if r.status_code in (401, 402, 429):
                    break
        except requests.RequestException as e:
            print(f"Request attempt {i+1} failed: {e}")
        time.sleep(2**i)
    raise RuntimeError("OpenRouter generation failed after retries")

# --- Fallback generator (if API missing or fails) ---
def generate_text_local_fallback(title: str) -> str:
    intro = f"В этой статье рассматривается «{title}». Я опишу ключевые концепции, практические примеры и дам рекомендации."
    sections = []
    sections.append("## Введение\n" + " ".join([intro]*2))
    sections.append("## Основные идеи\n" + "Здесь описаны основные подходы, архитектуры и ключевые понятия.")
    sections.append("## Практическая часть\n" + "Пошаговый пример и рекомендации для внедрения.")
    sections.append("## Заключение\n" + "Короткое резюме и направления для дальнейшего чтения.")
    return "\n\n".join(sections)

# --- Main creation logic ---
def create_post():
    ensure_dirs()
    title = random.choice(PROMPTS)
    slug = slugify(title)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{today}-{slug}.md"
    filepath = POSTS_DIR / filename

    # Generate or reuse image
    existing = pick_existing_image()
    if existing:
        imgname = f"{today}-{slug}{existing.suffix}"
        imgpath = IMG_DIR / imgname
        # copy existing to new name (to avoid overwriting)
        try:
            with open(existing, "rb") as src, open(imgpath, "wb") as dst:
                dst.write(src.read())
            print("Reused existing image:", existing.name)
        except Exception as e:
            print("Failed to copy existing image:", e)
            imgpath = IMG_DIR / f"{today}-{slug}.png"
            download_random_image(imgpath)
    else:
        imgpath = IMG_DIR / f"{today}-{slug}.png"
        ok = download_random_image(imgpath)
        if not ok:
            # If download failed, leave image empty (Hugo templates should handle absence)
            imgpath = None

    # Generate article text
    content = None
    if OPENROUTER_API_KEY:
        try:
            content = generate_text_via_openrouter(title)
        except Exception as e:
            print("OpenRouter failed:", e)
            content = generate_text_local_fallback(title)
    else:
        print("OPENROUTER_API_KEY not set — using local fallback text.")
        content = generate_text_local_fallback(title)

    # Build YAML front matter
    yaml_front = [
        "---",
        f'title: "{title.replace(\'"\', "\\\"")}"',
        f'date: "{datetime.utcnow().isoformat()}Z"',
        'draft: false',
    ]
    if imgpath:
        yaml_front.append(f'image: "{("/" + str(imgpath).replace(os.path.sep, "/"))}"')
    yaml_front.append("---\n")

    # Compose full markdown
    md = "\n".join(yaml_front) + content + "\n"

    # Write file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        print("Created post:", filepath)
    except Exception as e:
        print("Failed to write post:", e)
        raise

if __name__ == "__main__":
    create_post()
