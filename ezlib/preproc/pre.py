import os
import fitz  # PyMuPDF for PDF handling
import pypandoc
import docx
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from bs4 import BeautifulSoup
import logging
from tqdm import tqdm

# Tesseract OCR configuration
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Ensure log directory exists
log_dir = os.path.join("ezcache", "logs")
os.makedirs(log_dir, exist_ok=True)

# Set up logging to file in ezcache/logs/
log_file_path = os.path.join(log_dir, "conversion_log.txt")
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger("preprocess_logger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

def convert_to_text(file_path):
    """
    Converts a file to plain text based on its extension.

    Parameters:
        file_path (str): Path to the input file.

    Returns:
        str: Extracted text.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    try:
        if ext == '.txt':
            logger.info(f"Reading plain text file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        
        elif ext == '.pdf':
            logger.info(f"Extracting text from PDF: {file_path}")
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text("text")
            return text

        elif ext == '.docx':
            logger.info(f"Extracting text from DOCX: {file_path}")
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)

        elif ext in ['.doc', '.rtf', '.docx']:
            logger.info(f"Converting {ext.upper()} with Pandoc: {file_path}")
            return pypandoc.convert_file(file_path, 'plain')

        elif ext == '.html':
            logger.info(f"Parsing HTML content: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                return soup.get_text()

        else:
            raise ValueError(f"Unsupported format: {ext} for file {file_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to process {file_path}. Error: {e}")

def extract_from_scanned_pdf(file_path):
    """
    Performs OCR on each page of a scanned PDF.

    Parameters:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text with page markers.
    """
    logger.info(f"Starting OCR for scanned PDF: {file_path}")
    images = convert_from_path(file_path)
    text = ""
    for i, image in enumerate(images):
        page_text = pytesseract.image_to_string(image)
        text += f"--- Page {i + 1} ---\n{page_text}\n"
    return text

def preprocess_file(file_path):
    """
    Extracts text content from a file, falling back to OCR for scanned PDFs.

    Parameters:
        file_path (str): Path to the file.

    Returns:
        str: Extracted text, or an empty string on failure.
    """
    try:
        text = convert_to_text(file_path)
        if not text:
            raise RuntimeError("No content found.")
        return text

    except RuntimeError as e:
        if file_path.lower().endswith(".pdf"):
            logger.warning(f"Text extraction failed for {file_path}, retrying with OCR. Error: {e}")
            try:
                return extract_from_scanned_pdf(file_path)
            except Exception as e:
                logger.error(f"OCR failed for {file_path}. Error: {e}")
                return ""
        else:
            logger.error(f"Failed to process {file_path}. Skipping. Error: {e}")
            return ""

def preprocess_all(directory, verbose=False):
    """
    Processes all files in a directory to extract text, saving results in "ezcache/mirror/<dir_path>".

    Parameters:
        directory (str): Directory containing files to process.
        verbose (bool): If True, logs are shown in the console.
    """
    mirror_dir = os.path.join("ezcache", "mirror", directory)
    console_handler = logging.StreamHandler()

    if verbose:
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    logger.info(f"Starting batch conversion. Source: {directory}, Target: {mirror_dir}")

    # Gather all files in directory
    all_files = [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files]

    # Process files with progress bar
    for file_path in tqdm(all_files, desc="Converting files", unit="file"):
        relative_path = os.path.relpath(os.path.dirname(file_path), directory)
        target_dir = os.path.join(mirror_dir, relative_path)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, f"{os.path.splitext(os.path.basename(file_path))[0]}.txt")

        try:
            text = preprocess_file(file_path)
            if text:
                with open(target_file, 'w', encoding='utf-8') as output_file:
                    output_file.write(text)
                logger.info(f"Saved text: {file_path} -> {target_file}")
            else:
                logger.warning(f"No content extracted from {file_path}. Possible unsupported format.")

        except Exception as e:
            logger.error(f"Error processing {file_path}. Skipping. Error: {e}")

    if verbose:
        logger.removeHandler(console_handler)
