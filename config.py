import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram and OpenAI API tokens
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GIGACHAT_PASSWORD = os.getenv("GIGACHAT_PASSWORD")

# Bot configuration
MAX_MESSAGE_LENGTH = 280  # Maximum length of bot's response
RESPONSE_DELAY = 2  # Delay in seconds before bot responds

# Ensure the environment variables are set
if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not GIGACHAT_PASSWORD:
    raise ValueError(
        "Please set the TELEGRAM_TOKEN and OPENAI_API_KEY environment variables in the .env file."
    )
