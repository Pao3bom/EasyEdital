import os
import re
import csv
import pandas as pd
from math import log
from tqdm import tqdm
from collections import defaultdict

CACHE_DIRECTORY = '~/.cache/easyedital'


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


def build_count(
        filepath: str, output_directory: str = CACHE_DIRECTORY,
        save: bool = True, return_dict: bool = False) -> dict | pd.DataFrame:
    """
    Computes the word counts of the text file provided by the path.

    Parameters:
        filepath (str): Path to the file that will be counted.
        save (bool): Flag to save the count in a csv in the same directory as
        the original file.
        return_dict: Flag to return a dictionary instead of a pandas DataFrame.

    Returns:
        Dictionary containing the words and their respective counts.
    """

    if output_directory[-1] == '/':
        output_directory = output_directory[:-1]

    filename, extension = os.path.splitext(filepath)

    if extension != 'txt':
        print(f'{filepath} is not a text file')
        return {}

    count = defaultdict
    with open(filepath, 'r') as f:
        text = f.read()
        text = format_text(text)

        text = [x for x in text.split() if len(x) > 0]

        for word in text:
            count[word] += 1

    count_df = pd.DataFrame(count.items(), columns=['word', 'count'])
    count_df.sort_values(by='count', ascending=False, inplace=True)

    if save:
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        count_df.to_csv(
            f'{output_directory}/{os.path.basename(filename)}.csv', index=False)

    if return_dict:
        return count

    return count_df


def build_total_counts(
        files: list[str], cache_directory: str = CACHE_DIRECTORY,
        only_total: bool = False) -> None:
    """
    Computes the word counts of all text files in the provided 
    directory and saves them to a CSV in the same directory.

    Parameters:
        files (list[str]): List of files to use during counting.
        cache_directory (str): Output path and name.
        only_total (bool): Flag to only save the total count, discarding individual counts.
    """

    if cache_directory[-1] == '/':
        cache_directory += 'total_count.csv'

    elif os.path.splitext(cache_directory)[1] != '.csv':
        cache_directory += '.csv'

    total_count = defaultdict(int)
    doc_count = defaultdict(int)

    for file in tqdm(files, total=len(files), desc='Counting words...'):
        count_dict = build_count(file, save=not only_total, return_dict=True)

        for word, count in count_dict.items():
            total_count[word] += count
            doc_count[word] += 1

    total_count_df = pd.DataFrame(
        total_count.items(), columns=['word', 'total count'])
    total_count_df.sort_values(by='count', ascending=False, inplace=True)

    total_count_df['document frequency'] = total_count_df['word'].map(
        doc_count)

    total_count_df.to_csv(cache_directory, index=False)


def validate_word(word: str, frequency: int, min_frequency=3):
    word = re.sub(r'[^\w0-9]+', '', word, flags=re.UNICODE)

    if len(word) == 0 or word.isnumeric() or frequency < min_frequency:
        return False
    else:
        return True


def luhn_cut(data: list, lower: float, upper: float):
    lower_cut = len(data) * lower
    upper_cut = len(data) * upper

    return data[int(lower_cut):int(upper_cut)]


def cut_data(
        data: list, lower: float, upper: float, output: str,
        save_stopwords: bool = False, simple_name: bool = True,
        min_frequency: int = 3) -> None:
    """
    Separates keywords from stopwords and saves them to CSV.

    Parameters:
        data (list): List of tuples of words and their counts respectively.
        lower (float): Cut of lowest values.
        upper (float): Cut of highest values.
        output (str): Directory where the keywords and stopwords will be saved.
        save_stopwords (bool): Flag to save stopwords.
        simple_name (bool): Flag to use simpler names that hide the lower and 
        upper cut details.
        min_frequency (int): Minimum frequency for a word to be considered a
        keyword.
    """

    data_cut = luhn_cut(data, lower, upper)

    keywords = [x for x in data_cut if validate_word(
        x[0], x[1], min_frequency)]

    filepath = f'{output}/keywords'
    if not simple_name:
        filepath += '-{lower:.2f}-{upper:.2f}'

    filepath += '.csv'

    with open(filepath, 'w') as f:
        writer = csv.writer(f)

        for word, count in keywords:
            writer.writerow([word, count])

    if save_stopwords:
        stopwords = set([x for x in data]) - set(keywords)

        filepath = f'{output}/stopwords'
        if not simple_name:
            filepath += '-{lower:.2f}-{upper:.2f}'

        filepath += '.csv'

        with open(filepath, 'w') as f:
            writer = csv.writer(f)

            for word, count in stopwords:
                writer.writerow([word, count])


def generate_keywords(
        files: list[str], output_directory: str = CACHE_DIRECTORY,
        save_counts: bool = True, save_stopwords: bool = False,
        upper_cut=0.01, lower_cut=0.5):
    """
    Generates keywords from the files provided. Saves them to a CSV
    containing the words, their total count and the number in which they
    are found.

    Parameters:
        files (list): List of files to be processed.
        output_directory (str): Directory where the files generated
        will be saved.
        save_counts (bool): Saves the indivivual word counts of
        each file.
        save_stopwords (bool): Saves the stopwords generated.
        lower_cut (float): Cut of lowest values.
        upper_cut (float): Cut of highest values.
    """

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    savepath = output_directory

    if os.path.splitext(savepath)[1] != '.csv':
        savepath += '.csv'

    elif directory[-1] == '/':
        directory += 'total_count.csv'

    if not os.path.isfile(savepath):
        build_total_counts(files, savepath, only_total=not save_counts)

    data = []
    with open(savepath, 'r') as f:
        reader = csv.reader(f)

        next(reader)

        data = [[row[0], int(row[1])] for row in reader if row[0] != '']

    cut_data(data, upper_cut, lower_cut,
             output_directory, save_stopwords=save_stopwords)


def tf_idf(total_frequency, qtd_docs, local_frequency):
    return total_frequency * log((qtd_docs + 1) / (local_frequency + 1))


def generate_tdidf(
        filepath: str, keywords: dict,
        cache_directory: str = CACHE_DIRECTORY):
    """
    Generates a TF-IDF value for each keyword in the given file.

    Parameters:
        filepath (str): Path to the file.
        keywords (dict): Dictionary of valid keywords containing (Word) => (Global sum, Local sum)
        for the given file. That is, each keyword should come with its global count across the
        files and the count in the given file.
        cache_directory (str): Directory where the files of the program are being saved.
    """

    if cache_directory[-1] == '/':
        cache_directory = cache_directory[:-1]

    if not os.path.isdir(cache_directory):
        os.makedirs(cache_directory)

    text_words = []
    if os.path.isfile(f'{cache_directory}/{os.path.splitext(filepath)[0]}.csv'):
        with open(f'{cache_directory}/{os.path.basename(filepath)}.csv', 'r') as f:
            reader = csv.reader(f)
            text_words = [row for row in reader]

    else:
        text_words = list(build_count(filepath, return_dict=True))

    text_keywords = [row for row in text_words if row[0] in keywords.keys()]

    text_tfidf = {}
    for word, count in text_keywords:
        text_tfidf[word] = tf_idf(keywords[word][0], keywords[word][1], count)
    
    os.makedirs(f'{cache_directory}/{filepath}/', exist_ok=True)
    with open(f'{cache_directory}/{filepath}/tfidf.csv') as f:
        writer = csv.writer(f)

        for word, value in text_tfidf.values():
            writer.writerow([word, value])
    
    
