import asyncio
import logging
import signal
import sys
import traceback
from bot.telegram_handler import TelegramHandler
from config import TELEGRAM_TOKEN

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}. Stopping the bot...")
    asyncio.get_event_loop().stop()


async def main():
    logger.info("Starting the Telegram bot...")
    handler = TelegramHandler(TELEGRAM_TOKEN)

    try:
        # Register the signal handler
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)

        # Start the bot
        await handler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt.")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("Bot has been stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # The KeyboardInterrupt is caught in the main function
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
