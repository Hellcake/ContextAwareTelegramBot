import logging
import asyncio
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from .decision_maker import DecisionMaker
from language.russian_processor import RussianProcessor


class TelegramHandler:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.decision_maker = DecisionMaker()
        self.russian_processor = RussianProcessor()
        self._is_running = False
        self._stop_event = asyncio.Event()
        self.conversation_history = []
        self.last_human_message_time = 0
        self.last_bot_message_time = 0
        self.group_chat_id = None
        self.proactive_messaging_task = None

    async def start_command(self, update: Update, context):
        self.group_chat_id = update.effective_chat.id
        await update.message.reply_text(
            "Бот запущен и готов к работе в групповом чате!"
        )
        logging.info(f"Bot started in chat ID: {self.group_chat_id}")

    async def handle_message(self, update: Update, context):
        if not update.message or not update.message.text:
            logging.info("Received an update without a text message. Ignoring.")
            return

        chat_type = update.message.chat.type
        message = update.message.text
        user = update.effective_user.first_name

        logging.info(f"Received message in {chat_type} chat from {user}: {message}")

        if chat_type not in ["group", "supergroup"]:
            logging.info(
                f"Message received in {chat_type} chat. Bot only responds in group chats."
            )
            return

        self.group_chat_id = update.effective_chat.id

        try:
            processed_message = self.russian_processor.process(message)
            logging.info(f"Processed message: {processed_message}")

            # Add the message to conversation history
            self.conversation_history.append(
                {"user": user, "message": processed_message}
            )
            # Keep only the last 20 messages
            self.conversation_history = self.conversation_history[-20:]

            # Update last human message time
            self.last_human_message_time = time.time()

            should_respond = await self.decision_maker.should_respond(
                self.conversation_history
            )
            logging.info(f"Decision to respond: {should_respond}")

            if should_respond:
                response = await self.decision_maker.generate_response(
                    self.conversation_history, target_user=user
                )
                logging.info(f"Generated response: {response}")
                await update.message.reply_text(response)
                logging.info(f"Bot responded in the group chat")
                # Add bot's response to conversation history
                self.conversation_history.append({"user": "Bot", "message": response})
                # Update last bot message time
                self.last_bot_message_time = time.time()

        except Exception as e:
            logging.error(f"Error processing message: {str(e)}", exc_info=True)
            await update.message.reply_text("Произошла ошибка при обработке сообщения.")

    async def proactive_messaging(self):
        logging.info("Proactive messaging loop started")
        while self._is_running:
            try:
                current_time = time.time()
                should_initiate = await self.decision_maker.should_initiate(
                    current_time,
                    self.last_human_message_time,
                    self.last_bot_message_time,
                )
                logging.info(f"Should initiate proactive message: {should_initiate}")

                if should_initiate and self.group_chat_id:
                    message = await self.decision_maker.initiate_conversation(
                        self.conversation_history
                    )
                    logging.info(f"Attempting to send proactive message: {message}")
                    await self.application.bot.send_message(
                        chat_id=self.group_chat_id, text=message
                    )
                    self.conversation_history.append(
                        {"user": "Bot", "message": message}
                    )
                    self.last_bot_message_time = current_time
                    logging.info(f"Bot initiated conversation: {message}")
                else:
                    logging.info("Conditions not met for proactive message")
            except Exception as e:
                logging.error(f"Error in proactive messaging: {str(e)}", exc_info=True)
            await asyncio.sleep(5)

    async def error_handler(self, update: Update, context):
        logging.error(
            f"Exception while handling an update: {context.error}", exc_info=True
        )

    async def start(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self.application.add_error_handler(self.error_handler)

        logging.info("Starting bot polling...")
        await self.application.initialize()
        await self.application.start()
        self._is_running = True

        try:
            await self.application.updater.start_polling()
            logging.info("Bot is running. Press Ctrl+C to stop.")

            # Start proactive messaging
            self.proactive_messaging_task = asyncio.create_task(
                self.proactive_messaging()
            )

            await self._stop_event.wait()  # Wait until stop_event is set
        finally:
            await self.stop()

    async def stop(self):
        if self._is_running:
            logging.info("Stopping bot...")
            self._is_running = False
            self._stop_event.set()  # Signal the polling to stop

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
            logging.info("Bot has been stopped.")
        else:
            logging.info("Bot is not running.")
