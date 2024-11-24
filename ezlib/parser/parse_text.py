import os
import asyncio
import aiofiles
from .too_many_extensions import parse_doc, parse_rtf, parse_pdf, parse_docx, parse_html, parse_txt


async def parse_text(file_path, temp_dir=None):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().strip()

    match ext:
        case '.txt':
            return await parse_txt(file_path)

        case '.pdf':
            return await asyncio.to_thread(parse_pdf, file_path)

        case '.docx':
            return await asyncio.to_thread(parse_docx, file_path)
        
        case '.doc':
            # NOTE: When i tried to run this code asynchrously, it was throwing random errors sometimes
            return parse_doc(file_path, temp_dir=temp_dir)

        case '.rtf':
            return await asyncio.to_thread(parse_rtf, file_path)

        case '.html':
            return await parse_html(file_path)
            
        # case '.json' | '.csv' | '.png' | '.jpg' | '.htm' | '.download' | "" | ".css":
        #     return ""

        case _:
            raise ValueError(f"Unsupported file type: {ext}")