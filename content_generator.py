
#!/usr/bin/env python3
import os, requests, random, json
from datetime import datetime

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
    "ai brain made of circuits, glowing blue and purple, cyber style",
    "machine learning concept art, futuristic hologram, sci-fi aesthetics",
]

def generate_text(title):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role":"system","content":"Ты пишешь статьи для блога про ИИ и технологии. Стиль — обзор, урок или мастер-класс."},
            {"role":"user","content":f"Напиши статью на тему: {title}"}
        ]
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return "Ошибка генерации статьи."

def generate_image(prompt, filename):
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ','%20')}"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        path = os.path.join(IMG_DIR, filename)
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return path
    return None

def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)

    title = random.choice(PROMPTS)
    content = generate_text(title)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}-{title.replace(' ','-')}.md"
    imgname = f"{today}.png"
    imgpath = generate_image(random.choice(IMAGE_PROMPTS), imgname)

    with open(os.path.join(POSTS_DIR, filename), "w") as f:
        f.write(f"---\ntitle: \"{title}\"\ndate: {today}\n---\n\n")
        if imgpath:
            f.write(f"![{title}](/images/gallery/{imgname})\n\n")
        f.write(content)

if __name__ == "__main__":
    main()
