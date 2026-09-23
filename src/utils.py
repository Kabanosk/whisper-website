import os


def safe_remove(path: str):
    """Delete a file, silently ignoring errors if it's already gone.

    :param path: Path to the file to delete.
    """
    try:
        os.remove(path)
    except OSError:
        pass
