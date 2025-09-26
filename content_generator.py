import os
import re
import random
import requests
from datetime import datetime
from time import sleep
from PIL import Image
from io import BytesIO

# Папки
POSTS_DIR = "content/posts"
IMG_DIR = "static/images/gallery"

# Промпты для статей
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

# Промпты для изображений
IMAGE_PROMPTS = [
    "futuristic neural network visualization, neon cyberpunk style, high tech background",
    "AI lab with holographic screens, neon lights",
    "neural network abstract digital art",
]

# Проверка API ключа
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("Переменная окружения OPENROUTER_API_KEY не найдена!")

# Создаём папки, если нет
os.makedirs(POSTS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

def sanitize_slug(title: str) -> str:
    """Превращает заголовок в безопасный slug"""
    slug = title.lower()
    slug = re.sub(r'[^a-zа-я0-9\- ]', '', slug)
    slug = slug.replace(" ", "-")
    return slug

def generate_text(prompt: str, retries=3) -> str:
    """Генерация текста через OpenRouter с повторными попытками"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Ты пишешь статьи для блога про ИИ и технологии. Стиль — обзор, урок или мастер-класс."},
            {"role": "user", "content": f"Напиши статью на тему: {prompt}"}
        ],
        "max_tokens": 2000
    }

    for attempt in range(retries):
        r = requests.post(url, headers=headers, json=data)
        if r.status_code == 200:
            resp = r.json()
            if "choices" in resp and len(resp["choices"]) > 0:
                return resp["choices"][0]["message"]["content"]
            else:
                raise RuntimeError(f"API вернул некорректный ответ: {resp}")
        else:
            print(f"Попытка {attempt+1} не удалась: {r.text}")
            sleep(2)
    raise RuntimeError(f"Не удалось получить ответ от OpenRouter API после {retries} попыток")

def generate_image(prompt: str, filename: str):
    """Скачивание изображения по промпту"""
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ','%20')}"
    r = requests.get(url)
    if r.status_code == 200:
        img = Image.open(BytesIO(r.content))
        img.save(os.path.join(IMG_DIR, filename))
    else:
        print(f"Ошибка загрузки изображения: {r.status_code}")

def create_post():
    """Создаёт статью и сохраняет Markdown файл"""
    title = random.choice(PROMPTS)
    slug = sanitize_slug(title)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}-{slug}.md"

    print(f"Генерация статьи: {title}")
    content = generate_text(title)

    # Генерация изображения
    img_prompt = random.choice(IMAGE_PROMPTS)
    img_filename = f"{today}-{slug}.png"
    generate_image(img_prompt, img_filename)

    # Front Matter для Hugo (TOML)
    safe_title = title.replace('"', '\\"').replace('\n', ' ').strip()
    with open(os.path.join(POSTS_DIR, filename), "w", encoding="utf-8") as f:
        f.write("+++\n")
        f.write(f'title = "{safe_title}"\n')
        f.write(f'date = "{today}"\n')
        f.write(f'image = "images/gallery/{img_filename}"\n')
        f.write("draft = false\n")
        f.write("+++\n\n")
        f.write(content)

    print(f"Статья создана: {filename} с изображением {img_filename}")

if __name__ == "__main__":
    create_post()
