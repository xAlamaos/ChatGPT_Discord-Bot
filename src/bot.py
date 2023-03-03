# Imports section
import discord
from discord import app_commands
import os
from src import responses
from src import log


logger = log.setup_logger(__name__)
# Default values for Private and ReplyAll modes
isPrivate = False
isReplyAll = False


class Client(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/chat | /help")


async def send_message(message, user_message):
    global isReplyAll
    if not isReplyAll:
        author = message.user.id
        await message.response.defer(ephemeral=isPrivate)
    else:
        author = message.author.id
    try:
        response = '> **' + user_message + '** - <@' + \
            str(author) + '> \n\n'
        response = f"{response}{await responses.handle_response(user_message)}"
        char_limit = 1900
        if len(response) > char_limit:
            # Splits the answer into smaller parts under 1900 characters each(Discord limit is 2000)
            if "```" in response:
                # Splits the response if the code block exists
                parts = response.split("```")

                for i in range(0, len(parts)):
                    if i % 2 == 0:
                        if isReplyAll:
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
                                # Splits the line at the 50th character
                                formatted_code_block += line[:char_limit] + "\n"
                                line = line[char_limit:]
                            formatted_code_block += line + "\n"  # Add the line and seperate with new line

                        # Sends the code block in a separate message
                        if len(formatted_code_block) > char_limit+100:
                            code_block_chunks = [formatted_code_block[i:i+char_limit]
                                                 for i in range(0, len(formatted_code_block), char_limit)]
                            for chunk in code_block_chunks:
                                if isReplyAll:
                                    await message.channel.send("```" + chunk + "```")
                                else:
                                    await message.followup.send("```" + chunk + "```")
                        else:
                            if isReplyAll:
                                await message.channel.send("```" + formatted_code_block + "```")
                            else:
                                await message.followup.send("```" + formatted_code_block + "```")
            else:
                response_chunks = [response[i:i+char_limit] for i in range(0, len(response), char_limit)]
                for chunk in response_chunks:
                    if isReplyAll:
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
                        
        else:
            if isReplyAll:
                await message.channel.send(response)
            else:
                await message.followup.send(response)
    except Exception as e:
        if isReplyAll:
            await message.channel.send("> **Error: Something went wrong, please try again later!**")
        else:
            await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while trying to send message: {e}")


async def send_prompt(client):
    config_dir = os.path.abspath(__file__ + "/../../")
    prompt = "prompt.txt"
    prompt_path = os.path.join(config_dir, prompt)
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r") as f:
                prompt = f.read()
                if discord_channel_id:
                    logger.info(f"Sending starting prompt with size {len(prompt)}")
                    response_message = await responses.handle_response(prompt)
                    channel = client.get_channel(int(discord_channel_id))
                    await channel.send(response_message)
                    logger.info(f"Starting prompt response:{response_message}")
                else:
                    logger.info("No Channel selected. Skipping the initial prompt.")
        else:
            logger.info(f"No {prompt}. Skipping the initial prompt.")
    except Exception as e:
        logger.exception(f"Error while trying to send the initial prompt: {e}")


def run_discord_bot():
    client = Client()

    @client.event
    async def on_ready():
        await send_prompt(client)
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        global isReplyAll
        if isReplyAll:
            await interaction.followup.defer(ephemeral=False)
            await interaction.followup.send("> **Warn: You are already on replyAll mode. If you want to use slash "
                                            "command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou are already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
        await send_message(interaction, user_message)

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
            await interaction.followup.send(
                "> **Warn: You are already on private mode. If you want to switch to public mode, use `/public`**")

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
            await interaction.followup.send(
                "> **Warn: You are already on public mode. If you want to switch to private mode, use `/private`**")
            logger.info("You are already on public mode!")

    @client.tree.command(name="replyall", description="Toggle replyAll access")
    async def replyall(interaction: discord.Interaction):
        global isReplyAll
        await interaction.response.defer(ephemeral=False)
        if isReplyAll:
            await interaction.followup.send("> **Info: The bot will now only answer to the slash command `/chat`."
                                            " If you want to switch back to replyAll mode, use `/replyAll` again.**")
            logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
        else:
            await interaction.followup.send("> **Info: The bot will now answer to all messages in the server. "
                                            "If you want to switch back to normal mode, use `/replyAll` again.**")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")
        isReplyAll = not isReplyAll
    
    @client.tree.command(name="reset", description="Wipes the entire ChatGPT conversation history")
    async def reset(interaction: discord.Interaction):
        responses.chatbot.reset_chat()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **Info: ChatGPT conversation history has been wiped.**")
        logger.warning("\x1b[31mChatGPT bot has been successfully wiped\x1b[0m")
        await send_prompt(client)

    @client.tree.command(name="help", description="Show help for the bot")
    async def _help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":ring_buoy:**___BASIC COMMANDS___** \n
        **Chat with ChatGPT**
        - `/chat [message]`
        **ChatGPT switch to public mode**
        - `/public` 
        **ChatGPT switch between replyall mode and default mode**
        - `/replyall`
        **Clear ChatGPT conversation history**
        - `/reset`\n
        For complete documentation, please visit https://github.com/xAlamaos/ChatGPT-Discord-Bot""")
        logger.info("\x1b[31mSomeone needs help!\x1b[0m")

    @client.event
    async def on_message(message):
        if isReplyAll:
            if message.author == client.user:
                return
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
            await send_message(message, user_message)
    
    token = os.getenv("DISCORD_BOT_TOKEN")
    client.run(token)
