import asyncio
import logging
import signal
import traceback
from bot.telegram_handler import TelegramHandler
from config import TELEGRAM_TOKEN

# Установка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """
    Обработчик сигналов.

    :param sig: Полученный сигнал
    :param frame: Текущий фрейм
    """
    logger.info(f"Получен сигнал {sig}. Остановка бота...")
    asyncio.get_event_loop().stop()


async def main():
    """
    Главная функция.

    """
    logger.info("Запуск Telegram бота...")
    handler = TelegramHandler(TELEGRAM_TOKEN)

    try:
        # Регистрация обработчика сигналов
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)

        # Запуск бота
        await handler.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал от клавиатуры.")
    except Exception as e:
        logger.error(f"Нераспознанная ошибка: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # SIGINT будет пойман в функции main
    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}")
        logger.error(traceback.format_exc())
