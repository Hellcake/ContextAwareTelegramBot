import logging
import asyncio
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from .decision_maker import DecisionMaker
from config import RESPONSE_DELAY
from language.russian_processor import RussianProcessor


class TelegramHandler:
    def __init__(self, token):
        # Инициализация приложения Telegram с помощью предоставленного токена
        self.application = Application.builder().token(token).build()
        self.decision_maker = DecisionMaker()
        self.russian_processor = RussianProcessor()
        self._is_running = False
        self._stop_event = asyncio.Event()
        self.conversation_history = []  # История сообщений
        self.last_human_message_time = (
            time.time()
        )  # Время последнего сообщения от человека
        self.last_bot_message_time = time.time()  # Время последнего сообщения от бота
        self.current_time = time.time()
        self.group_chat_id = None
        self.proactive_messaging_task = None

    async def start_command(self, update: Update, context):
        # Обработка команды /start
        self.group_chat_id = update.effective_chat.id
        await update.message.reply_text(
            "Бот запущен и готов к работе в групповом чате!"
        )
        logging.info(f"Bot started in chat ID: {self.group_chat_id}")

    async def handle_message(self, update: Update, context):
        # Обработка текстовых сообщений
        if not update.message or not update.message.text:
            logging.info("Получено обновление без текстового сообщения. Игнорируется.")
            return

        chat_type = update.message.chat.type
        message = update.message.text
        user = update.effective_user.first_name

        logging.info(f"Получено сообщение в {chat_type} чате от {user}: {message}")

        if chat_type not in ["group", "supergroup"]:
            logging.info(
                f"Сообщение получено в {chat_type} чате. Бот отвечает только в групповых чатах."
            )
            return

        self.group_chat_id = update.effective_chat.id

        processed_message = self.russian_processor.process(message)

        # Добавление сообщения в историю
        self.conversation_history.append({"user": user, "message": processed_message})
        # Хранить только последние 20 сообщений
        self.conversation_history = self.conversation_history[-20:]

        # Обновление времени последнего сообщения от человека
        self.last_human_message_time = time.time()

        should_respond = await self.decision_maker.should_respond(
            self.conversation_history, self.current_time, self.last_bot_message_time
        )

        logging.info(f"Решение ответить: {should_respond}")

        if should_respond:
            await asyncio.sleep(RESPONSE_DELAY)  # Небольшая задержка перед ответом
            response = await self.decision_maker.generate_response(
                self.conversation_history, target_user=user
            )
            await update.message.reply_text(response)
            logging.info(f"Бот ответил в групповом чате")
            # Добавление ответа бота в историю
            self.conversation_history.append({"user": "Bot", "message": response})
            # Обновление времени последнего сообщения от бота
            self.last_bot_message_time = time.time()

    async def proactive_messaging(self):
        # Цикл проактивных сообщений
        logging.info("Запущен цикл проактивных сообщений")
        while self._is_running:
            try:
                current_time = time.time()
                should_initiate = await self.decision_maker.should_initiate(
                    current_time,
                    self.last_human_message_time,
                    self.last_bot_message_time,
                )
                logging.info(
                    f"Нужно ли инициировать проактивное сообщение: {should_initiate}"
                )

                if should_initiate and self.group_chat_id:
                    message = await self.decision_maker.initiate_conversation(
                        self.conversation_history
                    )
                    await self.application.bot.send_message(
                        chat_id=self.group_chat_id, text=message
                    )
                    self.conversation_history.append(
                        {"user": "Bot", "message": message}
                    )
                    self.last_bot_message_time = current_time
                    logging.info(f"Бот инициировал разговор: {message}")
                else:
                    logging.info("Условия не выполнены для проактивного сообщения")
            except Exception as e:
                logging.error(
                    f"Ошибка в проактивных сообщениях: {str(e)}", exc_info=True
                )
            await asyncio.sleep(60)  # Проверка каждую минуту

    async def start(self):
        # Запуск обработки команд и сообщений
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        logging.info("Запуск опроса бота...")
        await self.application.initialize()
        await self.application.start()
        self._is_running = True

        try:
            await self.application.updater.start_polling()
            logging.info("Бот работает. Нажмите Ctrl+C для остановки.")

            # Запуск проактивных сообщений
            self.proactive_messaging_task = asyncio.create_task(
                self.proactive_messaging()
            )

            await self._stop_event.wait()  # Ожидание установки stop_event
        finally:
            await self.stop()

    async def stop(self):
        # Остановка бота
        if self._is_running:
            logging.info("Остановка бота...")
            self._is_running = False
            self._stop_event.set()  # Сигнал к остановке опроса

            if self.proactive_messaging_task:
                self.proactive_messaging_task.cancel()
                try:
                    await self.proactive_messaging_task
                except asyncio.CancelledError:
                    pass

            if self.application.updater.running:
                await self.application.updater.stop()

            await self.application.stop()
            await self.application.shutdown()
            logging.info("Бот остановлен.")
        else:
            logging.info("Бот не работает.")
