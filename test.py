from ezlib import EzManager




def main():
    print('\n\n')
    print('=' * 50)
    print("Running test.py")
    watch_dir = "data"
    cache_dir = "cache"
    manager = EzManager(watch_dir, cache_dir)
    manager.preprocess()
    
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

if __name__ == "__main__":
    main()
