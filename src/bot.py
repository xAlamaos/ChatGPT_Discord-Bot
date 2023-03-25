import discord
import os
import openai
from random import randrange
from discord import app_commands
from src import responses
from src import log
from src import art
from src import personas


logger = log.setup_logger(__name__)
isPrivate = False


class Client(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/chat | /help")


async def send_message(message, user_message):
    is_reply_all = os.getenv("REPLYING_ALL")
    if is_reply_all == "False":
        author = message.user.id
        await message.response.defer(ephemeral=isPrivate)
    else:
        author = message.author.id
    try:
        response = (f'> **{user_message}** - <@{str(author)}' + '> \n\n')
        chat_model = os.getenv("CHAT_MODEL")
        if chat_model == "OFFICIAL":
            response = f"{response}{await responses.official_handle_response(user_message)}"

        elif chat_model == "UNOFFICIAL":
            response = f"{response}{await responses.unofficial_handle_response(user_message)}"
        char_limit = 1900

        if len(response) > char_limit:
            # Splits the answer into smaller parts under 1900 characters each(Discord limit is 2000)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")

                for i in range(len(parts)):
                    if i % 2 == 0:
                        if is_reply_all == "True":
                            await message.channel.send(parts[i])
                        else:
                            await message.followup.send(parts[i])
                    # Sends the code block in a seperate message
                    else:
                        # Odd-numbered parts are code blocks
                        code_block = parts[i].split("\n")
                        formatted_code_block = ""
                        for line in code_block:
                            while len(line) > char_limit:
                                # Split the line at the 50th character
                                formatted_code_block += line[:char_limit] + "\n"
                                line = line[char_limit:]
                            formatted_code_block += line + "\n"  # Add the line and seperate with new line

                        # Send the code block in a separate message
                        if len(formatted_code_block) > char_limit+100:
                            code_block_chunks = [formatted_code_block[i:i+char_limit]
                                                 for i in range(0, len(formatted_code_block), char_limit)]
                            for chunk in code_block_chunks:
                                if is_reply_all == "True":
                                    await message.channel.send(f"```{chunk}```")
                                else:
                                    await message.followup.send(f"```{chunk}```")
                        elif is_reply_all == "True":
                            await message.channel.send(f"```{formatted_code_block}```")
                        else:
                            await message.followup.send(f"```{formatted_code_block}```")
            else:
                response_chunks = [response[i:i+char_limit]
                                   for i in range(0, len(response), char_limit)]
                for chunk in response_chunks:
                    if is_reply_all == "True":
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
        elif is_reply_all == "True":
            await message.channel.send(response)
        else:
            await message.followup.send(response)
    except Exception as e:
        if is_reply_all == "True":
            await message.channel.send("> **Error: Something went wrong, please try again later!**")
        else:
            await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")


async def send_start_prompt(client):
    import os.path

    config_dir = os.path.abspath(f"{__file__}/../../")
    prompt_name = 'prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
                if discord_channel_id:
                    logger.info(f"Send starting prompt with size {len(prompt)}")
                    chat_model = os.getenv("CHAT_MODEL")
                    response = ""
                    if chat_model == "OFFICIAL":
                        response = f"{response}{await responses.official_handle_response(prompt)}"
                    elif chat_model == "UNOFFICIAL":
                        response = f"{response}{await responses.unofficial_handle_response(prompt)}"
                    channel = client.get_channel(int(discord_channel_id))
                    await channel.send(response)
                    logger.info(f"Starting prompt response:{response}")
                else:
                    logger.info("No Channel selected. Skip sending starting prompt.")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():
    client = Client()

    @client.event
    async def on_ready():
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        is_reply_all = os.getenv("REPLYING_ALL")
        if is_reply_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send("> **Warn: You are already on replyAll mode. If you want to use slash "
                                            "command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou are already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({channel})")
        await send_message(interaction, message)

    @client.tree.command(name="private", description="Toggle private access")
    async def private(interaction: discord.Interaction):
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if not isPrivate:
            isPrivate = not isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send("> **Info: The answers will now be sent via private message. "
                                            "If you want to switch back to public mode, use `/public`**")
        else:
            logger.info("You are already on private mode!")
            await interaction.followup.send("> **Warn: You are already on private mode. "
                                            "If you want to switch to public mode, use `/public`**")

    @client.tree.command(name="public", description="Toggle public access")
    async def public(interaction: discord.Interaction):
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if isPrivate:
            isPrivate = not isPrivate
            await interaction.followup.send("> **Info: The answer will be sent directly to the channel. "
                                            "If you want to switch back to private mode, use `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send("> **Warn: You are already on public mode. "
                                            "If you want to switch to private mode, use `/private`**")
            logger.info("You already on public mode!")

    @client.tree.command(name="replyall", description="Toggle replyAll access")
    async def replyall(interaction: discord.Interaction):
        is_reply_all = os.getenv("REPLYING_ALL")
        os.environ["REPLYING_ALL_DISCORD_CHANNEL_ID"] = str(interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if is_reply_all == "True":
            os.environ["REPLYING_ALL"] = "False"
            await interaction.followup.send("> **Info: The bot will now only answer to the slash command `/chat`."
                                            " If you want to switch back to replyAll mode, use `/replyAll` again.**")
            logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
        elif is_reply_all == "False":
            os.environ["REPLYING_ALL"] = "True"
            await interaction.followup.send("> **Info: The bot will now answer to all messages in the server. "
                                            "If you want to switch back to normal mode, use `/replyAll` again.**")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")

    @client.tree.command(name="chat-model", description="Switch different chat model")
    @app_commands.choices(choices=[
        app_commands.Choice(name="Official GPT-3.5", value="OFFICIAL"),
        app_commands.Choice(name="Ofiicial GPT-4.0", value="OFFICIAL-GPT4"),
        app_commands.Choice(name="Website ChatGPT-3.5", value="UNOFFICIAL"),
        app_commands.Choice(name="Website ChatGPT-4.0", value="UNOFFICIAL-GPT4"),
    ])
    async def chat_model(interaction: discord.Interaction, choices: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if choices.value == "OFFICIAL":
            os.environ["GPT_ENGINE"] = "gpt-3.5-turbo"
            os.environ["CHAT_MODEL"] = "OFFICIAL"
            responses.chatbot = responses.get_chatbot_model("OFFICIAL")
            await interaction.followup.send("> **Info: You are now using the Official GPT-3.5 model.**\n")
            logger.warning("\x1b[31mSwitch to OFFICIAL GPT-3.5 model\x1b[0m")
        elif choices.value == "OFFICIAL-GPT4":
            os.environ["GPT_ENGINE"] = "gpt-4"
            os.environ["CHAT_MODEL"] = "OFFICIAL"
            responses.chatbot = responses.get_chatbot_model("OFFICIAL")
            await interaction.followup.send("> **Info: You are now using the Official GPT-4.0 model.**\n")
            logger.warning("\x1b[31mSwitch to OFFICIAL GPT-4.0 model\x1b[0m")
        elif choices.value == "UNOFFICIAL":
            os.environ["GPT_ENGINE"] = "gpt-3.5-turbo"
            os.environ["CHAT_MODEL"] = "UNOFFICIAL"
            responses.chatbot = responses.get_chatbot_model("UNOFFICIAL")
            await interaction.followup.send("> **Info: You are now using the unofficial ChatGPT-3.5 model.**\n")
            logger.warning("\x1b[31mSwitch to UNOFFICIAL(Website) GPT-3.5 model\x1b[0m")
        elif choices.value == "UNOFFICIAL-GPT4":
            os.environ["GPT_ENGINE"] = "gpt-4"
            os.environ["CHAT_MODEL"] = "UNOFFICIAL"
            responses.chatbot = responses.get_chatbot_model("UNOFFICIAL")
            await interaction.followup.send("> **Info: You are now using the unofficial ChatGPT-4.0 model.**\n")
            logger.warning("\x1b[31mSwitch to UNOFFICIAL(Website) GPT-4.0 model\x1b[0m")

    @client.tree.command(name="reset", description="Complete reset ChatGPT conversation history")
    async def reset(interaction: discord.Interaction):
        model = os.getenv("CHAT_MODEL")
        if model == "OFFICIAL":
            responses.chatbot.reset()
        elif model == "UNOFFICIAL":
            responses.chatbot.reset_chat()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **Info: I have forgotten everything.**")
        personas.current_persona = "standard"
        logger.warning(
            "\x1b[31mChatGPT bot has been successfully reset\x1b[0m")
        await send_start_prompt(client)

    @client.tree.command(name="help", description="Show help for the bot")
    async def _help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":ring_buoy:**___BASIC COMMANDS___** \n
        **Chat with ChatGPT**
        - `/chat [message]`
        **Generates an image with the Dalle2 model**
        - `/draw [prompt]`
        **Switch between optionals ChatGPT personas**
        - `/switchpersona [persona]`
                `random`: Picks a random persona
                `chatgpt`: Standard chatGPT mode
                `dan`: Dan Mode 11.0, infamous Do Anything Now Mode
                `sda`: Superior DAN has even more freedom in DAN Mode
                `confidant`: Evil Confidant, evil trusted confidant
                `based`: BasedGPT v2, sexy gpt
                `oppo`: OPPO says exact opposite of what chatGPT would say
                `dev`: Developer Mode, v2 Developer mode enabled
        
        **ChatGPT switch to private mode**
        - `/private`
        **ChatGPT switch to public mode**
        - `/public`
        **ChatGPT switch between replyall mode and default mode**
        - `/replyall`
        **Clear ChatGPT conversation history**
        - `/reset`
         **Switch between Official/Unofficial ChatGPT mode**
        - `/chat-model`
                `OFFICIAL`: GPT-3.5 model
                `UNOFFICIAL`: Website ChatGPT

        For complete documentation, please visit https://github.com/xAlamaos/ChatGPT_Discord-Bot""")
        logger.info("\x1b[31mSomeone needs help!\x1b[0m")

    @client.tree.command(name="draw", description="Generate an image with the Dalle2 model")
    async def draw(interaction: discord.Interaction, *, prompt: str):
        is_reply_all = os.getenv("REPLYING_ALL")
        if is_reply_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send("> **Warn: You are already on replyAll mode. If you want to use slash "
                                            "command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou are already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return

        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /draw [{prompt}] in ({channel})")

        await interaction.response.defer(thinking=True)
        try:
            path = await art.draw(prompt)

            files = discord.File(path, filename="image.png")
            title = '> **' + prompt + '**\n'
            embed = discord.Embed(title=title)
            embed.set_image(url="attachment://image.png")

            await interaction.followup.send(file=files, embed=embed)

        except openai.InvalidRequestError:
            await interaction.followup.send("> **Warn: Inappropriate request**")
            logger.info(f"\x1b[31m{username}\x1b[0m made an inappropriate request.!")

        except Exception as e:
            await interaction.followup.send("> **Warn: Something went wrong**")
            logger.exception(f"Error while generating image: {e}")

    @client.tree.command(name="switchpersona", description="Switch between optional chatGPT personas")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Random", value="random"),
        app_commands.Choice(name="Standard", value="standard"),
        app_commands.Choice(name="Do Anything Now 11.0", value="dan"),
        app_commands.Choice(name="Superior Do Anything", value="sda"),
        app_commands.Choice(name="Evil Confidant", value="confidant"),
        app_commands.Choice(name="BasedGPT v2", value="based"),
        app_commands.Choice(name="OPPO", value="oppo"),
        app_commands.Choice(name="Developer Mode v2", value="dev")
    ])
    async def chat(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        is_reply_all = os.getenv("REPLYING_ALL")
        if is_reply_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send("> **Warn: You are already on replyAll mode. If you want to use slash "
                                            "command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou are already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(f"\x1b[31m{username}\x1b[0m : '/switchpersona [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **Warn: Already set to `{persona}` persona**")

        elif persona == "standard":
            model = os.getenv("CHAT_MODEL")
            if model == "OFFICIAL":
                responses.chatbot.reset()
            elif model == "UNOFFICIAL":
                responses.chatbot.reset_chat()

            personas.current_persona = "standard"
            await interaction.followup.send(f"> **Info: Switched to `{persona}` persona**")

        elif persona == "random":
            choices = list(personas.PERSONAS.keys())
            choice = randrange(0, 6)
            chosen_persona = choices[choice]
            personas.current_persona = chosen_persona
            await responses.switch_persona(chosen_persona)
            await interaction.followup.send(f"> **Info: Switched to `{chosen_persona}` persona**")

        elif persona in personas.PERSONAS:
            try:
                await responses.switch_persona(persona)
                personas.current_persona = persona
                await interaction.followup.send(f"> **Info: Switched to `{persona}` persona**")
            except Exception as e:
                await interaction.followup.send("> **Error: Something went wrong, please try again later!**")
                logger.exception(f"Error while switching personas: {e}")

        else:
            await interaction.followup.send(f"> **Error: Not available persona: `{persona}`**")
            logger.info(f'{username} requested an unavailable persona: `{persona}`')

    @client.event
    async def on_message(message):
        is_reply_all = os.getenv("REPLYING_ALL")
        if is_reply_all == "True" and message.channel.id == int(os.getenv("REPLYING_ALL_DISCORD_CHANNEL_ID")):
            if message.author == client.user:
                return
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
            await send_message(message, user_message)

    token = os.getenv("DISCORD_BOT_TOKEN")

    client.run(token)
