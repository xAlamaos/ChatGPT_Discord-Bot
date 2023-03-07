# Import section
from revChatGPT.V1 import AsyncChatbot
from revChatGPT.V3 import Chatbot
from dotenv import load_dotenv
import os
global answer_message


load_dotenv()
openAI_email = os.getenv("OPENAI_EMAIL")
openAI_password = os.getenv("OPENAI_PASSWORD")
session_token = os.getenv("SESSION_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
engine = os.getenv("OPENAI_ENGINE")
chat_model = os.getenv("CHAT_MODEL")

if chat_model == "UNOFFICIAL":
    unofficial_chatbot = AsyncChatbot(config={"email": openAI_email, "password": openAI_password,
                                              "session_token": session_token})
elif chat_model == "OFFICIAL":
    offical_chatbot = Chatbot(api_key=openai_api_key, engine=engine)


async def official_handle_response(message) -> str:
    return offical_chatbot.ask(message)


async def unofficial_handle_response(message) -> str:
    global answer_message
    async for response in unofficial_chatbot.ask(message):
        answer_message = response["message"]
    return answer_message
