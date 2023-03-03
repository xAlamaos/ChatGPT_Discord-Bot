# ChatGPT Discord Bot developed by xAlamaos

> ### Make your own ChatGPT Discord bot
---

## Features

* `/chat [message]` Chat with ChatGPT
* `/private` Switches to private mode (Only user who chats can see the answer)
* `/public`  Switches to public mode (Default Mode. Everyone can see the answers)
* `/replyall`  Switches between replyall mode and default mode (replyall mode do not require slash command)
* `/reset` It wipes ChatGPT entire conversation history

> **Warning:**
> On the `replyall` mode, the bot will be constantly listening to your chat and will keep replying to it. If you intend to use such mode, be advised to restrict the bot to a specific channel only.

# Setup

## Step 1: Create a Discord bot

1. Go to https://discord.com/developers/applications create an application
2. Build a Discord bot under the application
3. Get the token from bot setting
4. Store the token to `.env` under the `DISCORD_BOT_TOKEN`
5. Turn MESSAGE CONTENT INTENT `ON`
6. Invite your bot to your server via OAuth2 URL Generator

## Step 2: ChatGPT Authentication - 2 approaches

### Email/Password authentication Mode
1. Create an account on https://chat.openai.com/chat

2. Type your email into `.env` file under `OPENAI_EMAIL`

3. Type your password into `.env` file under `OPENAI_PASSWORD`

4. You may proceed to step 3

### Session Token Authentication Mode
1. Go to https://chat.openai.com/chat and log in your account

2. Open console with `F12`

2. Open `Application` tab > Cookies

3. Copy the value for `__Secure-next-auth.session-token` from cookies and paste it in the `.env` file under `SESSION_TOKEN`

4. You may proceed to step 3

## Step 3: Run the bot on your Desktop

1. Download Python (https://www.python.org/ftp/python/3.11.2/python-3.11.2-amd64.exe);

2. Install Python (Make sure you tick `Add python.exe to PATH` and in the end select `Disable path lenght limit`);

3. Open the bot folder and execute the `INSTALL.bat` file;

4. Right click on the `start_bot.bat` file and send it to Desktop as to create a shortcut;

5. Execute the shortcut and bot will finally turn on.

> **Warning:**
> If the execution the `INSTALL.bat` or `start_bot.bat` files won't work, try uninstalling and installing again Python.


> **Aditional Note:**
> If you find any problems within the bot itself, you may contact me through email: alamaosoficial@gmail.com or through my Discord tag  **Alamaos#4363**

## Optional: Setup Initial Prompt

* As the program starts, the initial prompt will be sent to the ChatGPT OpenAI which will send an initial message one the bot is activated or reseted.
* The initial prompt allows you to verify if the services of OpenAI are Online.
* You can set it up by modifying the content in `prompt.txt` file into something else as you'd like.
* If you don't want such prompt, you may clear the whole text and save it.

* In order to have such prompt sent to your Discord server, you'll need to:
   1. Activate developer mode on Discord, through `User Settings`, `Advanced` and tick on `Developer Mode`.
   2. Right-click the channel you would want to receive the message, select `Copy  ID`
   3. Paste it into the `.env` file under `DISCORD_CHANNEL_ID`
