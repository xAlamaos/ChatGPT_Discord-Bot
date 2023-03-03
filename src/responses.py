# Import section
from revChatGPT.V1 import AsyncChatbot
from dotenv import load_dotenv
import os
global response_message


load_dotenv()
openAI_email = os.getenv("OPENAI_EMAIL")
openAI_password = os.getenv("OPENAI_PASSWORD")
session_token = os.getenv("SESSION_TOKEN")
chatbot = AsyncChatbot(config={"email": openAI_email, "password": openAI_password, "session_token": session_token})


async def handle_response(message) -> str:
    global response_message
    async for response in chatbot.ask(message):
        response_message = response["message"]

    return response_message
