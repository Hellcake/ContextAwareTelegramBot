import nltk
from nltk.tokenize import word_tokenize
import logging


class RussianProcessor:
    def __init__(self):
        """Инициализация класса RussianProcessor."""
        self.ensure_nltk_data()

    def ensure_nltk_data(self):
        """Проверка наличия необходимых данных NLTK и их загрузка при необходимости."""
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            logging.info("Загрузка необходимых данных NLTK...")
            nltk.download("punkt")

    def process(self, text):
        """
        Обработка текста: преобразование в нижний регистр, токенизация и сборка обратно в строку.

        :param text: Входной текст для обработки.
        :return: Обработанный текст.
        """
        logging.info(f"Обработка текста: {text}")

        # Преобразование в нижний регистр
        text = text.lower()
        logging.info(f"Текст в нижнем регистре: {text}")

        # Токенизация текста
        tokens = word_tokenize(text, language="russian")
        logging.info(f"Токенизированный текст: {tokens}")

        # Сборка токенов обратно в строку
        processed_text = " ".join(tokens)
        logging.info(f"Итоговый обработанный текст: {processed_text}")

        return processed_text
