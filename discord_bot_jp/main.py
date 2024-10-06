from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response

# Load our environment vars from somewhere safe
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
SUB_KEY: Final[str] = os.getenv('AZURE_SUB_KEY')
ENDPOINT: Final[str] = os.getenv('AZURE_ENDPOINT')
TRANSLATE_PATH: Final[str] = os.getenv('AZURE_TRANSLATE_PATH')

# Setup the bot
# Intents are the permissions that the bots need to see/respond to messages
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# Message functionality
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('Message was empty because intents were not enabled')
        return

    # Private messages will be prepended with ? character
    # := is like ternary operatory - if user_message[0] == '?', is_private is set to True
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        # If the message is private, send message to user directly, otherwise send it to channel
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e: # Best practice is be more specific with exception
        print(e) # Best practice Proper logging

# Handling the startup for our bot
@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

# Handling incoming messages
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    
    username: str = message.author
    user_message: str = message.content
    channel: str = message.channel

    print(f'[{channel}] {username}: "{user_message}"')
    await send_message(message, user_message)

# Main entry point
def main() -> None:
    client.run(token=DISCORD_TOKEN)

if __name__ == '__main__':
    main()
