import os
from .parse_text import parse_text
from .scan import scan_pdf




def is_pdf(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().strip()
    return ext == '.pdf'

def is_scanned_pdf(file_path, content):
    return (not content or content.isspace()) and is_pdf(file_path)



async def hard_parse(file_path, executor=None, temp_dir=None):
    # First try to parse the file as text
    text = await parse_text(file_path, temp_dir=temp_dir)
    
    # If no text was extracted, try to scan the file
    if is_scanned_pdf(file_path, text):
        text = await scan_pdf(file_path, executor)
        
    return text