import re
from collections import defaultdict


def format_text(text: str):
    """
    Processes the text so only letters, numbers and hyphens are manteined.

    Parameters:
        text (str): Input text.

    Returns:
        str: Formatted text, or an empty string on failure.
    """

    if len(text) == 0:
        return ''

    text = text.lower()
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'[^\w0-9- ]+', '', text, flags=re.UNICODE)

    return text


def count_words(text: str) -> dict:
    """
    Counts the occurrences of each word in a given text.

    Parameters:
        text (str): Input text to process.

    Returns:
        dict: Dictionary of words and their respective counts.
    """
    if not text:
        return {}

    text = format_text(text)  # Reuse the existing format_text function
    words = text.split()

    word_count = defaultdict(int)
    for word in words:
        word_count[word] += 1

    return word_count