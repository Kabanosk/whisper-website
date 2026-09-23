from datetime import timedelta

import srt
from deep_translator import GoogleTranslator

DEFAULT_MAX_CHARACTERS = 80


def make_srt_subtitles(segments: list, translate_to: str, max_chars: int):
    """Build an SRT subtitle document from transcription segments.

    :param segments: A list of segment objects returned by the model's
        transcribe function, each exposing ``start``, ``end``, and
        ``text`` attributes.
    :param translate_to: Target language to translate each segment's
        text into, or "no_translation" to keep the original text.
    :param max_chars: Maximum number of characters per subtitle chunk.

    :return: The fully composed SRT file contents.
    :rtype: str
    """
    subtitles = []
    for i, seg in enumerate(segments, start=1):
        start_time = seg.start
        end_time = seg.end

        text = translate_text(seg.text.strip(), translate_to) if translate_to != "no_translation" else seg.text.strip()

        text_chunks = split_text_by_punctuation(text, max_chars)

        duration = (end_time - start_time) / len(text_chunks)

        for j, chunk in enumerate(text_chunks):
            chunk_start = start_time + j * duration
            chunk_end = chunk_start + duration

            subtitle = srt.Subtitle(
                index=len(subtitles) + 1,
                start=timedelta(seconds=chunk_start),
                end=timedelta(seconds=chunk_end),
                content=chunk,
            )
            subtitles.append(subtitle)

    return srt.compose(subtitles)


def translate_text(text: str, translate_to: str):
    """Translate text into the target language via Google Translate.

    :param text: The source text to translate.
    :param translate_to: Target language, as accepted by deep_translator's
        GoogleTranslator (e.g. "english", "chinese (simplified)"). Source
        language is auto-detected.

    :return: The translated text.
    """
    return GoogleTranslator(source="auto", target=translate_to).translate(text=text)


def split_text_by_punctuation(text: str, max_length: int):
    """Split text into chunks no longer than max_length.

    :param text: The text to split.
    :param max_length: Maximum number of characters per chunk.

    :return: A list of text chunks, each stripped of surrounding whitespace.
    """
    chunks = []
    while len(text) > max_length:
        split_pos = max(text.rfind(p, 0, max_length) for p in [",", ".", "?", "!", " "] if p in text[:max_length])

        if split_pos == -1:
            split_pos = max_length

        chunks.append(text[: split_pos + 1].strip())
        text = text[split_pos + 1 :].strip()

    if text:
        chunks.append(text)

    return chunks
