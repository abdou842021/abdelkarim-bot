import html
from urllib.parse import quote

import requests
import eng_to_ipa as ipa
from deep_translator import GoogleTranslator

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


def get_word(message: Message) -> str:
    # /syn word
    if message.text:
        parts = message.text.split(maxsplit=1)

        if len(parts) > 1:
            return parts[1].strip().split()[0]

    # Reply to a message containing a word
    if message.reply_to_message:
        text = (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        ).strip()

        if text:
            return text.split()[0]

    return ""


def get_dictionary_data(word: str):
    url = (
        "https://api.dictionaryapi.dev/api/v2/entries/en/"
        + quote(word)
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data:
            return None

        return data[0]

    except Exception:
        return None


def get_datamuse(word: str, relation: str):
    try:
        response = requests.get(
            "https://api.datamuse.com/words",
            params={
                relation: word,
                "max": 10,
            },
            timeout=10,
        )

        response.raise_for_status()

        return [
            item["word"]
            for item in response.json()
            if item.get("word")
        ]

    except Exception:
        return []


def get_arabic_meaning(definition: str) -> str:
    try:
        return GoogleTranslator(
            source="en",
            target="ar"
        ).translate(definition)

    except Exception:
        return "لم يتم العثور على الترجمة"


def clean_words(words, original_word):
    result = []

    for word in words:
        word = word.strip()

        if (
            word
            and word.lower() != original_word.lower()
            and word.lower() not in [x.lower() for x in result]
        ):
            result.append(word)

    return result


@router.message(Command("syn"))
async def synonyms_command(message: Message):
    word = get_word(message)

    if not word:
        await message.reply(
            "⚠️ Please send a word after /syn.\n\n"
            "Example:\n"
            "/syn semester"
        )
        return

    data = get_dictionary_data(word)

    if not data:
        await message.reply(
            f"❌ I couldn't find the word: {word}"
        )
        return

    # =========================
    # WORD
    # =========================

    real_word = data.get("word", word)

    # =========================
    # PRONUNCIATION
    # =========================

    dictionary_ipa = ""

    for phonetic in data.get("phonetics", []):
        if phonetic.get("text"):
            dictionary_ipa = phonetic["text"]
            break

    try:
        second_ipa = ipa.convert(real_word)
    except Exception:
        second_ipa = ""

    # =========================
    # MEANING / DEFINITIONS
    # =========================

    meanings = data.get("meanings", [])

    first_definition = ""
    part_of_speech = ""

    for meaning in meanings:
        if not part_of_speech:
            part_of_speech = meaning.get("partOfSpeech", "")

        definitions = meaning.get("definitions", [])

        if definitions:
            first_definition = definitions[0].get(
                "definition",
                ""
            )

            if first_definition:
                break

    arabic_meaning = ""

    if first_definition:
        arabic_meaning = get_arabic_meaning(
            first_definition
        )

    # =========================
    # SYNONYMS
    # =========================

    synonyms = []

    for meaning in meanings:
        synonyms.extend(
            meaning.get("synonyms", [])
        )

    if len(synonyms) < 5:
        synonyms.extend(
            get_datamuse(real_word, "rel_syn")
        )

    synonyms = clean_words(
        synonyms,
        real_word
    )[:6]

    # =========================
    # ANTONYMS
    # =========================

    antonyms = []

    for meaning in meanings:
        antonyms.extend(
            meaning.get("antonyms", [])
        )

    if len(antonyms) < 5:
        antonyms.extend(
            get_datamuse(real_word, "rel_ant")
        )

    antonyms = clean_words(
        antonyms,
        real_word
    )[:6]

    # =========================
    # EXAMPLE
    # =========================

    example = ""

    for meaning in meanings:
        for definition in meaning.get(
            "definitions",
            []
        ):
            if definition.get("example"):
                example = definition["example"]
                break

        if example:
            break

    # =========================
    # LINKS
    # =========================

    encoded_word = quote(real_word)

    youglish_url = (
        "https://youglish.com/pronounce/"
        f"{encoded_word}/english"
    )

    playphrase_url = (
        "https://playphrase.me/#/search?q="
        f"{encoded_word}"
    )

    # =========================
    # FORMAT
    # =========================

    safe_word = html.escape(real_word)

    result = (
        f"🇬🇧 <b>{safe_word}</b>\n"
    )

    if dictionary_ipa:
        result += (
            f"<i>{html.escape(dictionary_ipa)}</i>"
        )

    if second_ipa and second_ipa != dictionary_ipa:
        result += (
            f"   🔊 <b>{html.escape(second_ipa)}</b>"
        )

    result += "\n"

    if arabic_meaning:
        result += (
            f"◀️ {html.escape(arabic_meaning)}"
        )

    if part_of_speech:
        result += (
            f"  <i>({html.escape(part_of_speech)})</i>"
        )

    result += "\n"

    if synonyms:
        result += (
            "🔹 <b>Syn:</b> "
            + html.escape(", ".join(synonyms))
            + "\n"
        )

    if antonyms:
        result += (
            "🔸 <b>Ant:</b> "
            + html.escape(", ".join(antonyms))
            + "\n"
        )

    if example:
        result += (
            f"📝 <b>Ex:</b> "
            f"{html.escape(example)}\n"
        )

    result += (
        f'🗣 <a href="{youglish_url}">YouGlish</a>   '
        f'🎬 <a href="{playphrase_url}">PlayPhrase</a>'
    )

    await message.reply(
        result,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
