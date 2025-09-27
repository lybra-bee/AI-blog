#!/usr/bin/env python3
import os
import json
import requests
import random
from datetime import datetime, timezone
import shutil
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont
import time
import logging
import argparse
import base64

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# Директории
POSTS_DIR = "content/posts"
IMAGES_DIR = "assets/images/posts"

# Убедимся, что папки существуют
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# API-ключи (проверь что они есть в переменных окружения)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not OPENROUTER_API_KEY:
    logging.warning("⚠️ Переменная окружения OPENROUTER_API_KEY не установлена")
if not GROQ_API_KEY:
    logging.warning("⚠️ Переменная окружения GROQ_API_KEY не установлена")


def generate_text(prompt: str, model="gpt-4o-mini") -> str:
    """
    Генерация текста через OpenRouter API
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    logging.info("🔹 Отправка запроса к OpenRouter...")
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        logging.error(f"❌ Ошибка OpenRouter API: {response.status_code} {response.text}")
        return ""

    result = response.json()
    return result["choices"][0]["message"]["content"]


def generate_image(prompt: str) -> str:
    """
    Генерация изображения через Groq API (или другой сервис)
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {"prompt": prompt}

    logging.info("🎨 Генерация изображения...")
    response = requests.post("https://api.groq.com/v1/images", headers=headers, json=data)

    if response.status_code != 200:
        logging.error(f"❌ Ошибка Groq API: {response.status_code} {response.text}")
        return ""

    result = response.json()
    img_b64 = result.get("data", [{}])[0].get("b64_json")

    if not img_b64:
        logging.error("❌ Пустой ответ при генерации изображения")
        return ""

    img_data = base64.b64decode(img_b64)

    filename = f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-image.png"
    filepath = os.path.join(IMAGES_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(img_data)

    logging.info(f"✅ Сохранено изображение: {filepath}")
    return f"/{filepath}"


def create_post():
    """
    Генерация статьи с картинкой
    """
    logging.info("📝 Генерация новой статьи...")

    title_prompt = "Придумай интересный заголовок для статьи о будущем искусственного интеллекта."
    title = generate_text(title_prompt).strip()

    article_prompt = f"Напиши статью под заголовком: {title}. Тема — нейросети, ИИ, технологии. Объем: 5-6 абзацев."
    content = generate_text(article_prompt).strip()

    image_prompt = f"Создай картинку для статьи: {title}"
    image_path = generate_image(image_prompt)

    # Имя файла
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # Frontmatter + контент
    frontmatter = [
        "---",
        f'title: "{title.replace("\"", "\\\"")}"',
        f"date: {datetime.now(timezone.utc).isoformat()}",
        f"image: {image_path}",
        "---",
        "",
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(frontmatter))
        f.write(content)

    logging.info(f"✅ Сохранена статья: {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1, help="Сколько статей сгенерировать")
    args = parser.parse_args()

    for _ in range(args.count):
        create_post()
        time.sleep(2)  # задержка между генерациями
