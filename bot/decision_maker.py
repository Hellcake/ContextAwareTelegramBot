import logging
import random
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from config import GEMINI_API_KEY

class DecisionMaker:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GEMINI_API_KEY)
        self.proactive_threshold = 300  # 5 minutes in seconds
        self.min_human_response_time = 60  # 1 minute in seconds

    async def should_respond(self, conversation_history, current_time, last_bot_message_time):
        if not conversation_history:
            return False

        last_message = conversation_history[-1]
        if last_message["user"] == "Bot":
            logging.info("Last message was from the bot. Not responding.")
            return False

        try:
            conversation_text = "\n".join(
                [f"{msg['user']}: {msg['message']}" for msg in conversation_history[-10:]]
            )
            time_since_last_bot = current_time - last_bot_message_time
            prompt = [
                f"""
                Вы - ИИ-ассистент в групповом чате Telegram. Ваша задача - анализировать контекст разговора и решать, нужно ли вам ответить.
                Внимательно изучите историю беседы и определите, есть ли необходимость в вашем участии.
                Проанализируйте следующую историю разговора и ответьте "Да" или "Нет" на вопрос, стоит ли вам вмешаться в беседу.
                
                Отвечайте "Да", если:
                1) Кто-то задал вопрос группе, на который вы можете дать полезный ответ
                2) В разговоре возникла пауза, и вы можете добавить что-то интересное по теме
                3) Обсуждается тема, в которую вы можете внести ценную информацию или новый взгляд
                4) Кто-то напрямую обратился к боту или упомянул его
                5) Есть возможность уточнить или развить мысль, высказанную участником беседы
                
                Отвечайте "Нет", если:
                1) Разговор идет активно и ваше вмешательство может быть неуместным
                2) Тема разговора личная или деликатная
                3) Ваш последний ответ был совсем недавно, и нет острой необходимости снова вступать в беседу, время с вашего последнего ответа: {time_since_last_bot}
                4) Обсуждение касается тем, в которых у вас нет достаточной компетенции
                
                История разговора (последние сообщения):
                
                {conversation_text}
                
                Ответьте только "Да" или "Нет".
                """
            ]
            response = self.llm.invoke(prompt)
            should_respond = response.content.lower().strip() == "да"
            logging.info(f"Decision to respond: {should_respond}")
            return should_respond
        except Exception as e:
            logging.error(f"Error in should_respond: {str(e)}", exc_info=True)
            return False

    async def should_initiate(self, current_time, last_human_message_time, last_bot_message_time):
        time_since_last_human = current_time - last_human_message_time
        time_since_last_bot = current_time - last_bot_message_time
        
        logging.info(f"Time since last human message: {time_since_last_human} seconds")
        logging.info(f"Time since last bot message: {time_since_last_bot} seconds")

        if time_since_last_human > self.min_human_response_time:
            logging.info("New message from human")
            return True

        if time_since_last_bot > self.proactive_threshold:
            logging.info("Enough time has passed since the last bot message")
            return True

        return False

    async def generate_response(self, conversation_history, target_user=None):
        logging.info(f"Generating response based on conversation history")
        
        try:
            conversation_text = "\n".join(
                [f"{msg['user']}: {msg['message']}" for msg in conversation_history[-10:]]
            )
            target_instruction = f"Обратитесь к пользователю {target_user} в своем ответе." if target_user else ""
            prompt = [
                f"""
                Вы - дружелюбный и умный ИИ-ассистент в групповом чате Telegram. Ваша задача - поддерживать 
                интересную и содержательную беседу, отвечая уместно и по существу. Используйте формальный стиль речи, 
                но будьте дружелюбны и открыты. Ваши ответы должны быть на русском языке.
                
                На основе предоставленной истории разговора, сгенерируйте релевантный и естественный ответ. 
                
                {target_instruction}
                
                Ваш ответ должен соответствовать следующим критериям:
                1) Быть кратким и по существу (не более 2-3 предложений)
                2) Соответствовать контексту и тону разговора
                3) Добавлять ценность к обсуждению (новая информация, интересный факт, уточняющий вопрос)
                4) Быть написанным на грамотном русском языке
                5) Поощрять дальнейшее обсуждение, если это уместно
                
                Избегайте:
                1) Повторения уже сказанного
                2) Использования сленга или неформальной лексики
                3) Высказывания категоричных суждений по спорным вопросам
                
                История разговора (последние сообщения):
                
                {conversation_text}
                
                Ваш ответ:
                """
            ]
            response = self.llm.invoke(prompt)
            generated_response = response.content.strip()
            logging.info(f"Generated response: {generated_response}")
            return generated_response
        except Exception as e:
            logging.error(f"Error in generate_response: {str(e)}", exc_info=True)
            return "Извините, произошла ошибка при генерации ответа."

    async def initiate_conversation(self, conversation_history):
        logging.info(f"Initiating conversation based on conversation history")
        last_message = conversation_history[-1]
        if last_message["user"] == "Bot":
            logging.info("Last message was from the bot. Not responding.")
            return False
        
        try:
            conversation_text = "\n".join(
                [f"{msg['user']}: {msg['message']}" for msg in conversation_history[-5:]]
            )
            prompt = [
                f"""
                Вы - инициативный ИИ-ассистент в групповом чате Telegram. Ваша задача - начать новую тему разговора 
                или продолжить существующую, основываясь на последних сообщениях. Ваше сообщение должно быть на русском языке.
                
                На основе предоставленной истории разговора, придумайте интересное сообщение, которое может 
                оживить беседу или начать новую увлекательную тему.
                
                Ваше сообщение должно соответствовать следующим критериям:
                1) Быть релевантным контексту предыдущего разговора или плавно переходить к новой теме
                2) Быть интригующим и способным вызвать отклик у участников чата
                3) Содержать открытый вопрос или утверждение, которое побуждает к обсуждению
                4) Быть написанным на грамотном русском языке
                5) Не превышать 2-3 предложения
                
                Возможные варианты начала сообщения:
                - "Кстати, я недавно узнал интересный факт о..."
                - "А что вы думаете о..."
                - "Интересно, как бы вы поступили, если бы..."
                - "Мне кажется, или в последнее время все чаще говорят о..."
                
                Последние сообщения в чате:
                
                {conversation_text}
                
                Ваше новое сообщение:
                """
            ]
            response = self.llm.invoke(prompt)
            initiated_message = response.content.strip()
            logging.info(f"Initiated message: {initiated_message}")
            return initiated_message
        except Exception as e:
            logging.error(f"Error in initiate_conversation: {str(e)}", exc_info=True)
            return "Извините, у меня возникли проблемы с генерацией новой темы. Возможно, кто-то из вас хочет предложить интересную тему для обсуждения?"