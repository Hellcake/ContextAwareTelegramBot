import re
import nltk
from nltk.tokenize import word_tokenize
import logging


class RussianProcessor:
    def __init__(self):
        self.ensure_nltk_data()

    def ensure_nltk_data(self):
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            logging.info("Downloading necessary NLTK data...")
            nltk.download("punkt")

    def process(self, text):
        logging.info(f"Processing text: {text}")

        # Convert to lowercase
        text = text.lower()
        logging.info(f"Lowercased text: {text}")

        # # Remove punctuation
        # text = re.sub(r'[^\w\s]', '', text)
        # logging.info(f"Text after removing punctuation: {text}")

        # Tokenize
        tokens = word_tokenize(text, language="russian")
        logging.info(f"Tokenized text: {tokens}")

        # Join tokens back into a string
        processed_text = " ".join(tokens)
        logging.info(f"Final processed text: {processed_text}")

        return processed_text
