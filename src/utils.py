import os
from datetime import timedelta

import ffmpeg
import numpy as np
import srt
from deep_translator import GoogleTranslator

DEFAULT_MAX_CHARACTERS = 80


def get_audio_buffer(filename: str, start: int, length: int):
    """Extract a slice of audio from a file as a normalized float32 array.

    :param filename: Path to the source audio file.
    :param start: Start offset in seconds.
    :param length: Duration in seconds to extract.

    :return: A 1-D numpy.ndarray of float32 samples in the range [-1.0, 1.0].
    """
    out, _ = (
        ffmpeg.input(filename, threads=0)
        .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=16000, ss=start, t=length)
        .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
    )

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


def transcribe_time_stamps(segments: list):
    """Render transcription segments as a plain-text timestamped log.

    :param segments: A list of segment objects returned by the model's
        transcribe function, each exposing ``start``, ``end``, and
        ``text`` attributes.

    :return: A single string with one line per segment, formatted as
        "<start> -> <end> : <text>".
    """
    string = ""
    for seg in segments:
        string += " ".join([str(seg.start), "->", str(seg.end), ": ", seg.text.strip(), "\n"])
    return string


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


def translate_text(text: str, translate_to: str):
    """Translate text into the target language via Google Translate.

    :param text: The source text to translate.
    :param translate_to: Target language, as accepted by deep_translator's
        GoogleTranslator (e.g. "english", "chinese (simplified)"). Source
        language is auto-detected.

    :return: The translated text.
    """
    return GoogleTranslator(source="auto", target=translate_to).translate(text=text)


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


def safe_remove(path: str):
    """Delete a file, silently ignoring errors if it's already gone.

    :param path: Path to the file to delete.
    """
    try:
        os.remove(path)
    except OSError:
        pass
