import json
import re
from collections import Counter


def format_text(text: str) -> str:
    """
    Formats the input text by:
    - Converting to lowercase
    - Replacing newlines with spaces
    - Removing punctuation except hyphens and numbers
    - Collapsing multiple spaces into a single space

    Args:
        text (str): Input text to format.

    Returns:
        str: Formatted text.
    """
    if not text:
        return ''

    text = text.lower()
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'[^\w0-9- ]+', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def count_words(text: str, sort_by: str = "frequency") -> dict[str, int]:
    """
    Counts the frequency of words in a given text.

    Args:
        text (str): Input text to process.
        sort_by (str, optional): Sorting method for the result ('alphabetical' or 'frequency').
                                 Defaults to None.

    Returns:
        dict[str, int]: Dictionary of word counts.
    """
    words = format_text(text).split()
    counts = Counter(words)

    if sort_by == "alphabetical":
        return dict(sorted(counts.items()))
    elif sort_by == "frequency":
        return dict(sorted(counts.items(), key=lambda x: -x[1]))
    
    return dict(counts)
