from types import SimpleNamespace

import pytest
import srt

from services.subtitles import make_srt_subtitles, split_text_by_punctuation


def _without_spaces(txt: str):
    return txt.replace(" ", "")


@pytest.mark.parametrize(
    ("text", "max_length"),
    [
        ("Hello, world. How are you today? Fine!", 15),
        ("这是一个没有空格的很长的中文句子", 5),
        ("abcdefgh ij", 5),
    ],
)
def test_split_chunks_fit_and_keep_all_text(text, max_length):

    chunks = split_text_by_punctuation(text, max_length)

    assert all(len(chunk) <= max_length for chunk in chunks)
    assert _without_spaces("".join(chunks)) == _without_spaces(text)


def test_split_short_text_is_returned_as_single_chunk():
    assert split_text_by_punctuation("Hi there", 80) == ["Hi there"]


def test_empty_segment_does_not_crash_and_is_skipped():
    segments = [
        SimpleNamespace(start=0.0, end=1.0, text="Hello"),
        SimpleNamespace(start=1.0, end=2.0, text="   "),
    ]

    result = make_srt_subtitles(segments, translate_to="no_translation", max_chars=80)

    assert [subtitle.content for subtitle in srt.parse(result)] == ["Hello"]
