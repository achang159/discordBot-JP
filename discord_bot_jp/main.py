import os

from typing import Final, List, Tuple, Dict
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text.models import TranslatedTextItem, TranslationLanguage
from azure.core.exceptions import HttpResponseError

# Load our environment vars from somewhere safe
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
AZURE_TEXT_TRANSLATION_API_KEY: Final[str] = os.getenv('AZURE_API_KEY')
AZURE_TEXT_TRANSLATOR_REGION: Final[str] = os.getenv('AZURE_REGION')
AZURE_TEXT_TRANSLATION_ENDPOINT : Final[str] = os.getenv('AZURE_ENDPOINT')

def create_text_translation_client_with_credential() -> TextTranslationClient:
    # [START create_text_translation_client_with_credential]
    credential = AzureKeyCredential(AZURE_TEXT_TRANSLATION_API_KEY)
    text_translator = TextTranslationClient(credential=credential, region=AZURE_TEXT_TRANSLATOR_REGION)
    # [END create_text_translation_client_with_credential]
    return text_translator

def get_supported_languages() -> Tuple[List[str], dict[str, TranslationLanguage]]:
    try:
        response = text_translator.get_supported_languages()
        supported_languages: List[str] = []
        supported_lang_tooltip: List[str] = []
        if response.translation is not None:
            #print("Translation Languages:")
            for key, value in response.translation.items():
                supported_languages.append(key)
                supported_lang_tooltip.append(f"{key}:\t{value.name}")

        # if response.transliteration is not None:
        #     print("Transliteration Languages:")
        #     for key, value in response.transliteration.items():
        #         print(f"{key} -- name: {value.name}, supported script count: {len(value.scripts)}")

        # if response.dictionary is not None:
        #     print("Dictionary Languages:")
        #     for key, value in response.dictionary.items():
        #         print(f"{key} -- name: {value.name}, supported target languages count: {len(value.translations)}")
        return supported_languages, supported_lang_tooltip
    
    except HttpResponseError as exception:
        if exception.error is not None:
            print(f"Error Code: {exception.error.code}")
            print(f"Message: {exception.error.message}")
        raise

async def print_supported_languages_tooltip(message: Message) -> None:
    if len(_supported_lang_tooltip) <= 0:
        await message.channel.send(f"ERROR: {_supported_lang_tooltip} has not been set.")
    else:
        await message.channel.send("Translation Languages:")
        await message.channel.send('\n'.join(_supported_lang_tooltip))

async def set_to_language(message: Message, to_language: str,) -> None:
    if to_language not in _supported_languages:
        await message.channel.send(f"Error: {to_language} not supported")
    else:
        await message.channel.send(f"Set translation language to {to_language}!")
        _to_language = to_language

# Globals (eventually add these into Client class)
_to_language: str = ""
_supported_languages: List[str] = []
_supported_lang_tooltip: List[str] = []
#Add dict to print name in tooltip

# Setup the bot
# Intents are the permissions that the bots need to see/respond to messages
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# Setup Azure text translator client
text_translator: TextTranslationClient = create_text_translation_client_with_credential()
_supported_languages, _supported_lang_tooltip = get_supported_languages()

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
        translated_text: List[TranslatedTextItem] = await translate_text(text_to_translate)
        
        if translated_text:
            for language in translated_text:
                for translation in language.translations:
                    await message.channel.send(translation.text)
        else:
            await message.channel.send('Error: Could not translate text.')
    
    elif message.content.startswith('!get_lang'):
        await print_supported_languages_tooltip(message)

    elif message.content.startswith('!set_lang'):
        if len(message.content) <= len('!set_lang '):
            await message.channel.send(f"ERROR: No language specified")
            await print_supported_languages_tooltip(message)
        else:
            to_language: str = message.content[len('!set_lang '):]
            await set_to_language(message, to_language)
    
    else:
        await send_message(message, user_message)

# Translation functionality
async def translate_text(text_to_translate: str) -> List[TranslatedTextItem]:
    try:
        print(f"{_to_language}")

        if _to_language == "":
            print(f"ERROR: {_to_language} is not a supported language. Try setting a language using !set_lang command.")
            return None
        
        # Prep body for API request
        body = [{
            'text': text_to_translate
        }]
        
        response: List[TranslatedTextItem] = text_translator.translate(
            body=body, to_language=_to_language
        )

        # TODO: Add test string to avoid calling API multiple times
        # text: TranslationText = "こんにちは、元気ですか。"
        # translation = TranslatedTextItem(translations=[text])
        # response: List[TranslatedTextItem]

        return response if response else None
        
    except HttpResponseError as exception:
        if exception.error is not None:
            print(f"Error Code: {exception.error.code}")
            print(f"Message: {exception.error.message}")
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
