import os

from typing import Final, List
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text.models import TranslatedTextItem, TranslationText

# Load our environment vars from somewhere safe
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
AZURE_TEXT_TRANSLATION_API_KEY: Final[str] = os.getenv('AZURE_API_KEY')
AZURE_TEXT_TRANSLATOR_REGION: Final[str] = os.getenv('AZURE_REGION')
AZURE_TEXT_TRANSLATION_ENDPOINT : Final[str] = os.getenv('AZURE_ENDPOINT')

def create_text_translation_client_with_credential():
    # [START create_text_translation_client_with_credential]
    credential = AzureKeyCredential(AZURE_TEXT_TRANSLATION_API_KEY)
    text_translator = TextTranslationClient(credential=credential, region=AZURE_TEXT_TRANSLATOR_REGION)
    # [END create_text_translation_client_with_credential]
    return text_translator

# Setup the bot
# Intents are the permissions that the bots need to see/respond to messages
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# Setup Azure text translator client
text_translator: TextTranslationClient = create_text_translation_client_with_credential()

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

    if message.content.startswith('!translate'):
        text_to_translate: str = message.content[len('!translate '):]
        translated_text: List[TranslatedTextItem] = await translate_text_to_japanese(text_to_translate)
        
        if translated_text:
            for language in translated_text:
                for translation in language.translations:
                    await message.channel.send(translation.text)
        else:
            await message.channel.send('Error: Could not translate text.')
    else:
        await send_message(message, user_message)

# Translation functionality
async def translate_text_to_japanese(text_to_translate: str) -> List[TranslatedTextItem]:
    try:
        from_language = "en"
        to_language = ["ja"]
        # Prep body for API request
        body = [{
            'text': text_to_translate
        }]
        
        response: List[TranslatedTextItem] = text_translator.translate(
            body=body, to_language=to_language, from_language=from_language
        )

        # TODO: Test string to avoid calling API multiple times
        # translations: TranslationText = "こんにちは、元気ですか。"
        # response: TranslatedTextItem = TranslatedTextItem(translations=[translations])

        return response if response else None
        
    except Exception as exception:
        if exception.error is not None:
            print(f"Exception: {exception}")
        raise

# Message functionality
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('Message was empty because intents were not enabled')
        return

    # Private messages will be prepended with ? character
    # := is like ternary operatory - if user_message[0] == '?', is_private is set to True
    if is_private := user_message.startswith('?'):
        user_message = user_message[1:]

    try:
        response: str = get_response(user_message)
        # If the message is private, send message to user directly, otherwise send it to channel
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e: # Best practice is be more specific with exception
        print(e) # Best practice Proper logging

# Main entry point
def main() -> None:
    client.run(token=DISCORD_TOKEN)

if __name__ == '__main__':
    main()
