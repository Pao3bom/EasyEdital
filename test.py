from ezlib import EzManager
import asyncio



def main():
    print('\n\n')
    print('=' * 50)
    print("Running test.py")
    watch_dir = "data"
    cache_dir = "cache"
    manager = EzManager(watch_dir, cache_dir)
    manager.preprocess()
    
    query = input("Enter a search query: ")
    results = asyncio.run(manager.search(query))
    
    print(results)
    
# # def main():
#     import pypandoc
#     result = pypandoc.convert_file("test.rtf", "plain")
#     print(result)

    
    
# if __name__ == "__main__":
# #     main()


# from striprtf.striprtf import rtf_to_text

# def main():
#     # Load the RTF file
#     with open("test.rtf", "r", encoding="utf-8") as file:
#         rtf_content = file.read()

#     # Extract text
#     plain_text = rtf_to_text(rtf_content)

#     print(plain_text)

# import os
# import subprocess
# from tempfile import NamedTemporaryFile
# from docx import Document as DocxDocument


# def extract_text_from_doc(filepath):
#     with NamedTemporaryFile(suffix="__TEMP__.docx", delete=False) as temp_file:
#         temp_docx_path = temp_file.name

#     try:
#         # Convert '.doc' to '.docx'
#         result = subprocess.run(
#             ['unoconv', '-f', 'docx', '-o', temp_docx_path, filepath],
#             check=True,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#         )
#         if result.returncode != 0:
#             raise RuntimeError(f"Unoconv failed: {result.stderr.decode()}")

#         # Extract text from the temporary .docx file
#         doc = DocxDocument(temp_docx_path)
#         text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
#     except Exception as e:
#         raise RuntimeError(f"Failed to extract text from .doc file: {e}")
#     finally:
#         # Cleanup
#         if os.path.exists(temp_docx_path):
#             os.remove(temp_docx_path)

#     return text


# def main():
#     print(extract_text_from_doc('test.doc'))

# import os
# import shutil
# import hashlib
# import subprocess
# from docx import Document as DocxDocument

# def extract_text_from_doc(filepath, retry_limit=5):
#     # Convert PosixPath to string if necessary
#     filepath = str(filepath)

#     # Ensure the file exists
#     if not os.path.exists(filepath):
#         raise FileNotFoundError(f"File not found: {filepath}")
    
#     # Hash the file path to avoid conflicts
#     hash = hashlib.md5(filepath.encode()).hexdigest()
#     temp_dir = os.path.join(os.path.dirname(filepath), f"_TEMP_{hash}")
#     os.makedirs(temp_dir, exist_ok=True)

#     temp_doc_path = os.path.join(temp_dir, os.path.basename(filepath))
#     predicted_docx_path = os.path.splitext(temp_doc_path)[0] + ".docx"

#     attempts = 0

#     while attempts <= retry_limit:
#         try:
#             # Copy the original file to the temporary directory
#             shutil.copy(filepath, temp_doc_path)
#             print(f"Attempt {attempts + 1}: Converting {temp_doc_path}")

#             # Convert .doc to .docx using LibreOffice
#             result = subprocess.run(
#                 ['libreoffice', '--headless', '--convert-to', 'docx', temp_doc_path, '--outdir', temp_dir],
#                 check=False,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#             )

#             # Check if conversion was successful
#             if result.returncode != 0 or not os.path.exists(predicted_docx_path):
#                 raise RuntimeError(
#                     f"LibreOffice failed for file `{filepath}`.\n"
#                     f"Command: {' '.join(result.args)}\n"
#                     f"Error: {result.stderr.decode()}"
#                 )

#             # Extract text from the converted .docx file
#             doc = DocxDocument(predicted_docx_path)
#             text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
#             print("Conversion and extraction successful!")
#             return text

#         except Exception as e:
#             print(f"Error during attempt {attempts + 1} for `{filepath}`: {e}")
#             attempts += 1
#             if attempts > retry_limit:
#                 raise RuntimeError(f"Failed to extract text from `{filepath}` after {retry_limit + 1} attempts.") from e
#         finally:
#             # Cleanup temporary files in the directory for each attempt
#             if os.path.exists(temp_dir):
#                 shutil.rmtree(temp_dir, ignore_errors=True)
                
                
# def main():
#     print(extract_text_from_doc('LMM - 2023. SECULT.  MINUTA EDITAIS. LEI PAULO GUSTAVO.doc'))

if __name__ == "__main__":
    main()
