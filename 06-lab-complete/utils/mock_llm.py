"""Simple mock LLM used for the lab."""

import random
import time


RESPONSES = {
    "docker": "Docker dong goi app va dependencies de deploy nhat quan.",
    "redis": "Redis giup luu state ngoai process de app stateless va scale duoc.",
    "deploy": "Deployment dua ung dung len moi truong public de nguoi dung truy cap.",
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay)
    lower_question = question.lower()
    for keyword, response in RESPONSES.items():
        if keyword in lower_question:
            return response

    defaults = [
        "Agent da nhan cau hoi va tra loi bang mock LLM.",
        "He thong dang hoat dong on dinh tren production flow gia lap.",
        "Day la phan hoi mau de ban tap trung vao deployment va reliability.",
    ]
    return random.choice(defaults)
