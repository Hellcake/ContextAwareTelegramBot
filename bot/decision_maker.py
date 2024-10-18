import logging
import random
import time
from gigachat import GigaChat
from config import GIGACHAT_PASSWORD


class DecisionMaker:
    def __init__(self):
        self.giga = GigaChat(credentials=GIGACHAT_PASSWORD, verify_ssl_certs=False)
        self.proactive_threshold = 300  # 5 minutes in seconds
        self.min_human_response_time = 60  # 1 minute in seconds

    async def should_respond(self, conversation_history):
        if not conversation_history:
            return False

        last_message = conversation_history[-1]
        print(last_message)
        if last_message["user"] == "Bot":
            logging.info("Last message was from the bot. Not responding.")
            return False

        try:
            conversation_text = "\n".join(
                [f"{msg['user']}: {msg['message']}" for msg in conversation_history]
            )
            prompt = f"""Вы - бот в групповом чате. Учитывая следующую историю разговора, решите, должны ли вы ответить.
            Отвечайте 'да', если:
            1) Кто-то задал вопрос группе
            2) В разговоре возникла пауза и вы можете добавить что-то интересное
            3) Вы можете добавить полезную информацию к обсуждаемой теме
            4) Кто-то напрямую обратился к боту или упомянул его
            Отвечайте 'нет' в противном случае.
            
            История разговора:
            {conversation_text}
            
            Ответьте только 'да' или 'нет'.
            """
            response = self.giga.chat(prompt)
            should_respond = response.choices[0].message.content.lower().strip() == "да"
            logging.info(f"Decision to respond: {should_respond}")
            return should_respond
        except Exception as e:
            logging.error(f"Error in should_respond: {str(e)}", exc_info=True)
            return False

    async def should_initiate(
        self, current_time, last_human_message_time, last_bot_message_time
    ):
        time_since_last_human = current_time - last_human_message_time
        time_since_last_bot = current_time - last_bot_message_time
        logging.info(f"Time since last human message: {time_since_last_human} seconds")
        logging.info(f"Time since last bot message: {time_since_last_bot} seconds")

        if time_since_last_human < 10 and time_since_last_bot > 10:
            logging.info("New message")
            should_initiate = True
            return should_initiate

        if time_since_last_bot < self.proactive_threshold:
            logging.info("Not enough time has passed since the last bot message")
            return False

        should_initiate = random.random() < 0.3  # 30% chance to initiate
        logging.info(f"Decision to initiate: {should_initiate}")
        return should_initiate

    async def generate_response(self, conversation_history, target_user=None):
        logging.info(f"Generating response based on conversation history")
        
        try:
            conversation_text = "\n".join(
                [f"{msg['user']}: {msg['message']}" for msg in conversation_history]
            )
            target_instruction = (
                f"Ваш ответ должен быть адресован пользователю {target_user}."
                if target_user
                else ""
            )
            prompt = f"""Вы - бот в групповом чате. Сгенерируйте релевантный и естественный ответ на основе следующей истории разговора.
            Ваш ответ должен быть кратким, дружелюбным и соответствовать контексту разговора.
            {target_instruction}
            Проанализируйте тему разговора, настроение участников и контекст перед формированием ответа.
            
            История разговора:
            {conversation_text}
            
            Ваш ответ:
            """
            response = self.giga.chat(prompt)
            generated_response = response.choices[0].message.content.strip()
            logging.info(f"Generated response: {generated_response}")
            return generated_response
        except Exception as e:
            logging.error(f"Error in generate_response: {str(e)}", exc_info=True)
            return "Извините, я не смог сгенерировать ответ."

    async def initiate_conversation(self, conversation_history):
        logging.info(f"Initiating conversation based on conversation history")
        
        try:
            conversation_text = "\n".join(
                [
                    f"{msg['user']}: {msg['message']}"
                    for msg in conversation_history[-5:]
                ]
            )  # Use last 5 messages for context
            prompt = f"""Вы - бот в групповом чате. Начните новую тему разговора или продолжите существующую, основываясь на последних сообщениях.
            Ваше сообщение должно быть интересным, релевантным и способным вовлечь участников в дискуссию.
            
            Последние сообщения в чате:
            {conversation_text}
            
            Ваше новое сообщение:
            """
            response = self.giga.chat(prompt)
            initiated_message = response.choices[0].message.content.strip()
            logging.info(f"Initiated message: {initiated_message}")
            return initiated_message
        except Exception as e:
            logging.error(f"Error in initiate_conversation: {str(e)}", exc_info=True)
            return "Кстати, у меня есть интересная мысль, но я не могу ее сформулировать. Может, кто-нибудь хочет обсудить что-нибудь?"
