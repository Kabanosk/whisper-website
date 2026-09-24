import pytest
from pydantic import ValidationError

from schemas.transcription import SubtitleFileType, TranscriptionRequest


@pytest.mark.parametrize("value", [0, -1, 501])
def test_max_characters_out_of_range_is_rejected(value):
    with pytest.raises(ValidationError, match="max_characters"):
        TranscriptionRequest(max_characters=value)


@pytest.mark.parametrize("value", [1, 500])
def test_max_characters_within_range_is_accepted(value):
    request = TranscriptionRequest(max_characters=value)

    assert request.max_characters == value


def test_unknown_model_type_is_rejected():
    with pytest.raises(ValidationError, match="model_type"):
        TranscriptionRequest(model_type="gigantic")


def test_unknown_file_type_is_rejected():
    with pytest.raises(ValidationError, match="file_type"):
        TranscriptionRequest(file_type="docx")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("captions", "captions"),
        ("captions.srt", "captions"),
        ("archive.tar.gz", "archive.tar"),
        ("my captions", "my_captions"),
        ("café", "caf_"),
        ("../../secret.srt", "secret"),
        ("C:\\Users\\me\\file.srt", "C__Users_me_file"),
    ],
)
def test_filename_is_sanitized(raw, expected):
    request = TranscriptionRequest(filename=raw)

    assert request.filename == expected


@pytest.mark.parametrize("raw", ["", "/", "dir/"])
def test_empty_filename_falls_back_to_default(raw):
    request = TranscriptionRequest(filename=raw)

    assert request.filename == "subtitles"


@pytest.mark.parametrize(
    ("timestamps", "file_type", "expected"),
    [
        (True, SubtitleFileType.SRT, "srt"),
        (True, SubtitleFileType.VTT, "vtt"),
        (False, SubtitleFileType.SRT, "txt"),
        (False, SubtitleFileType.VTT, "txt"),
    ],
)
def test_output_extension(timestamps, file_type, expected):
    request = TranscriptionRequest(timestamps=timestamps, file_type=file_type)

    assert request.output_extension == expected


def test_download_filename_combines_name_and_extension():
    request = TranscriptionRequest(filename="my captions.txt", timestamps=True, file_type=SubtitleFileType.VTT)

    assert request.download_filename == "my_captions.vtt"
