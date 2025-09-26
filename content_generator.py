#!/usr/bin/env python3
import os
import requests
import json
from datetime import datetime

# 🔑 Ключ OpenRouter (обязательно в GitHub Secrets: OPENROUTER_API_KEY)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
LLM_MODEL = "openai/gpt-4o-mini"  # можно заменить на "anthropic/claude-3.5-sonnet"

def generate_article():
    """Генерация статьи через OpenRouter"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = """
    Сгенерируй статью в формате Hugo:
    1) Заголовок (короткий и цепляющий)
    2) Текст статьи (3–5 абзацев, Markdown)
    Тема: искусственный интеллект, нейросети, будущее технологий.
    """

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "model": LLM_MODEL,
            "max_tokens": 500,  # ✅ ограничение, чтобы не упираться в лимит
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Некорректный JSON от OpenRouter: {resp.text}")

    if "choices" not in data:
        raise RuntimeError(f"Ошибка OpenRouter API: {json.dumps(data, ensure_ascii=False, indent=2)}")

    text = data["choices"][0]["message"]["content"]

    # Разделим заголовок и текст
    parts = text.strip().split("\n", 1)
    title = parts[0].replace("#", "").strip()
    content = parts[1].strip() if len(parts) > 1 else ""

    return title, content

def create_post():
    """Создание файла поста"""
    title, content = generate_article()

    today = datetime.now().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-").replace('"', "").replace("'", "")

    filename = f"content/posts/{today}-{slug}.md"
    os.makedirs("content/posts", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(f'title = "{title}"\n')
        f.write(f'date = "{today}"\n')
        f.write("draft = false\n")
        f.write("---\n\n")
        f.write(content)

    print(f"✅ Пост создан: {filename}")

if __name__ == "__main__":
    create_post()
