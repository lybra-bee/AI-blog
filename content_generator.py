#!/usr/bin/env python3
import os
import requests
import json
from datetime import datetime
import logging

# === Настройки ===
POSTS_DIR = "content/posts"
IMAGES_DIR = "static/images/posts"

# Ключи
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Модель для текста
LLM_MODEL = "openai/gpt-4o-mini"  # можно заменить на claude, llama, gemini через openrouter
# Модель для изображений
IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

# Убедимся, что папки есть
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)


def generate_article():
    """Генерация статьи через OpenRouter"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = """
    Сгенерируй статью в формате:
    1) Заголовок (короткий и цепляющий)
    2) Основной текст статьи (3–5 абзацев)

    Тема: нейросети, искусственный интеллект, будущее технологий.
    """

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )

    data = resp.json()
    text = data["choices"][0]["message"]["content"]

    # Разделим заголовок и текст
    parts = text.strip().split("\n", 1)
    title = parts[0].replace("#", "").strip()
    content = parts[1].strip() if len(parts) > 1 else ""

    return title, content


def generate_image(title, filename):
    """Генерация изображения через OpenRouter (Stable Diffusion)"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = f"Futuristic illustration for article about: {title}"

    resp = requests.post(
        "https://openrouter.ai/api/v1/images",
        headers=headers,
        json={"model": IMAGE_MODEL, "prompt": prompt},
        timeout=120,
    )

    if resp.status_code == 200:
        img_data = resp.content
        with open(filename, "wb") as f:
            f.write(img_data)
        logging.info(f"Изображение сохранено: {filename}")
    else:
        logging.error(f"Ошибка генерации изображения: {resp.text}")


def create_post():
    title, content = generate_article()
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-").replace("ё", "e")

    filename = os.path.join(POSTS_DIR, f"{date_str}-{slug}.md")
    image_name = f"{slug}.png"
    image_path = os.path.join(IMAGES_DIR, image_name)

    # Генерация изображения
    generate_image(title, image_path)

    # YAML frontmatter
    frontmatter = [
        "---",
        f'title: "{title}"',
        f"date: {date_str}",
        "draft: false",
        f"image: /images/posts/{image_name}",
        "---",
        "",
    ]

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(frontmatter))
        f.write(content)

    logging.info(f"Статья создана: {filename}")


if __name__ == "__main__":
    create_post()
