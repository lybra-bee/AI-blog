import os
import requests
import random
from datetime import datetime
from PIL import Image
from io import BytesIO

# ------------------------------
# Настройки
# ------------------------------
POSTS_DIR = "content/posts"
IMG_DIR = "static/images/gallery"

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
    "ai brain circuits, glowing neural network, futuristic style",
    "futuristic lab with holographic screens, sci-fi style",
]

# ------------------------------
# Проверка ключа
# ------------------------------
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ Не найден OPENROUTER_API_KEY в переменных окружения")

# ------------------------------
# Функции генерации текста
# ------------------------------
def generate_text(title, retries=3):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Ты пишешь статьи для блога про ИИ и технологии. Стиль — обзор, урок или мастер-класс."},
            {"role": "user", "content": f"Напиши статью на тему: {title}"}
        ]
    }

    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=data, timeout=30)
            r.raise_for_status()
            resp = r.json()
            if "choices" in resp:
                return resp["choices"][0]["message"]["content"]
            else:
                print(f"⚠️ Попытка {attempt+1}: нет ключа 'choices', ответ API: {resp}")
        except Exception as e:
            print(f"⚠️ Попытка {attempt+1} ошибка: {e}")
    return "Ошибка генерации статьи."

# ------------------------------
# Функция генерации изображения
# ------------------------------
def generate_image(prompt, filename):
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        os.makedirs(IMG_DIR, exist_ok=True)
        img.save(os.path.join(IMG_DIR, filename))
        print(f"✅ Изображение создано: {filename}")
        return filename
    except Exception as e:
        print(f"⚠️ Ошибка генерации изображения: {e}")
        return None

# ------------------------------
# Создание поста
# ------------------------------
def create_post():
    title = random.choice(PROMPTS)
    content = generate_text(title)

    # Дата
    today = datetime.now().strftime("%Y-%m-%d")

    # Создаём безопасный slug
    slug = (
        title.lower()
        .replace(" ", "-")
        .replace('"', "")
        .replace("'", "")
        .replace(":", "")
        .replace(",", "")
    )

    # Путь к файлу
    filename = f"{today}-{slug}.md"
    os.makedirs(POSTS_DIR, exist_ok=True)

    # Экранируем кавычки в заголовке
    safe_title = title.replace('"', '\\"')

    # Генерация поста с Front Matter TOML
    with open(os.path.join(POSTS_DIR, filename), "w", encoding="utf-8") as f:
        f.write("+++\n")
        f.write(f'title = "{safe_title}"\n')
        f.write(f'date = "{today}"\n')
        f.write("draft = false\n")
        f.write("+++\n\n")
        f.write(content)

    # Генерация изображения
    img_filename = f"{today}-{slug}.png"
    generate_image(random.choice(IMAGE_PROMPTS), img_filename)

    print(f"✅ Пост создан: {filename}")

# ------------------------------
# Главная функция
# ------------------------------
if __name__ == "__main__":
    create_post()
