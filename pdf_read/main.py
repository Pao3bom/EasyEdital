import os
import fitz  # PyMuPDF for PDFs
import pypandoc
from docx import Document
import docx

def convert_to_text(file_path):
    """
    Convert a PDF, DOC, or DOCX file to plain text.

    Parameters:
        file_path (str): The path to the input file.

    Returns:
        str: The plain text extracted from the file.
    """
    # Get file extension
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    
    # Handling .pdf files
    if file_extension == '.pdf':
        text = ""
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text")  # Extract text from each page
        doc.close()
        return text
    
    # Handling .docx files
    if file_extension == '.docx':
        try:
            doc = Document(file_path)
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            return text
        except Exception as e:
            print('Could not extract text from .docx file:', e)
            print('Trying to extract text using pypandoc...')
    
    # Handling .doc files or if pypandoc is available for broader support
    if file_extension == '.doc' or file_extension == '.docx':
        try:
            # Convert using Pandoc if available for broader format support
            text = pypandoc.convert_file(file_path, 'plain')
            return text
        except OSError:
            # Handle missing Pandoc
            raise ValueError("Pandoc is required for .doc files or broader format support. Please install it.")
        
    
    raise ValueError(f"Unsupported file format: {file_extension}. Supported formats: PDF, DOC, DOCX.")

# Example usage
try:
    text_content = convert_to_text("example.pdf")  # replace with your file
    print(text_content)
except ValueError as e:
    print(e)
