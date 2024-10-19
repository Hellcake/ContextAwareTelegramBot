import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Токены API Telegram и OpenAI
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GIGACHAT_PASSWORD = os.getenv("GIGACHAT_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Конфигурация бота
MAX_MESSAGE_LENGTH = 280  # Максимальная длина ответа бота
RESPONSE_DELAY = 2  # Задержка в секундах перед ответом бота

# Обеспечение настройки переменных окружения
if (
    not TELEGRAM_TOKEN
    or not OPENAI_API_KEY
    or not GIGACHAT_PASSWORD
    or not GEMINI_API_KEY
):
    raise ValueError(
        "Установите переменные окружения TELEGRAM_TOKEN, OPENAI_API_KEY, GIGACHAT_PASSWORD и GEMINI_API_KEY в файле .env."
    )
