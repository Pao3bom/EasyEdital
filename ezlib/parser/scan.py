import asyncio
import pytesseract
from pdf2image import convert_from_path



def scan_page(image, page_num):
    """OCR process for a single PDF page."""
    page_text = pytesseract.image_to_string(image)
    return f"--- Page {page_num} ---\n{page_text}\n"


async def scan_pdf(file_path, executor=None):
    images = await asyncio.to_thread(lambda: convert_from_path(file_path))

    loop = asyncio.get_running_loop()
    tasks = [
        loop.run_in_executor(executor, scan_page, image, i + 1)
        for i, image in enumerate(images)
    ]
    
    results = await asyncio.gather(*tasks)
    return "".join(results)