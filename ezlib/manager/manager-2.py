# import os
# import logging
# import asyncios
# import torch
# from sentence_transformers import SentenceTransformer
# from pathlib import Path
# from .helper import calculate_limits, store_file, read_file


# STD_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# STD_MODEL = 'ulysses-camara/legal-bert-pt-br'


# class EzManager:
#     def __init__(
#         self, 
#         watch_dir: str | Path, 
#         cache_dir: str | Path, 
#         max_threads=None, 
#         max_processes=None, 
#         model_name : str | None = None,
#     ) -> None:
#         self.__watch_dir = Path(watch_dir)
#         self.__cache_dir = Path(cache_dir)
        
#         self.__temp_dir = self.__cache_dir / "temp"
#         self.__files_dir = self.__cache_dir / "files"
#         self.__global_dir = self.__cache_dir / "global"
        
#         # Create the cache structure
#         os.makedirs(self.__global_dir, exist_ok=True)
#         os.makedirs(self.__files_dir, exist_ok=True)
#         os.makedirs(self.__temp_dir, exist_ok=True)

#         # Configure logging
#         logging.basicConfig(
#             level=logging.INFO,
#             format="%(asctime)s [%(levelname)s] %(message)s"
#         )
#         self.logger = logging.getLogger("EzManager")

#         # Set worker limits
#         self.__max_threads, self.__max_processes = calculate_limits(max_threads, max_processes)
        
#         # Initialize the embedding model
#         if model_name is None:
#             model_name = STD_MODEL
#         self.__model = SentenceTransformer(model_name, device="cuda" if torch.cuda.is_available() else "cpu")
        
#         # Material
#         self.__generators = {
#             'counts.csv': {},
#         }
        
#         self.__dependencies = {
#             'counts.csv': [('text.txt', 'local')],
#         }
        
#         # Global
#         self.__global_dependencies = {
#             'frequency.csv': [('text.txt', 'local')],
#         }
        
#         self.__global_generators = {}

    
#     def __property_path(self, file : Path, property : str):
#         return self.__files_dir / file.stem / property
    
#     async def __load_local_dependencies(self, file : Path, dependencies : list[str]):
#         return {k: await self.__fetch_property(file, k) for k, type in dependencies if type == 'local'}
    
#     async def __load_global_dependencies(self, dependencies : list[str]):
#         return {k: await self.__fetch_global_property(k) for k, type in dependencies if type == 'global'}
    
#     async def __load_dependencies(self, file : Path, dependencies : list[str]):
#         local_deps = await self.__load_local_dependencies(file, dependencies)
#         global_deps = await self.__load_global_dependencies(dependencies)
#         return {'local': local_deps, 'global': global_deps}
    
#     async def __gen_property(self, file : Path, property : str, io_exec, cpu_exec):
#         # NOTE: This function assumes that the file exists
        
#         # Make sure the property directory exists
#         p = self.__property_path(file, property)
#         os.makedirs(p.parent, exist_ok=True)
        
#         # Get the generator function
#         deps = self.__load_dependencies(file, self.__dependencies[property])
        
#         # Generate the property
#         gen = self.__generators[property]
#         data = await gen(file, deps, io_exec, cpu_exec)
        
#         # Write the data to the property file
#         await store_file(p, data)
        
#         # Return the data
#         return data
      
      
#     async def __fetch_property(self, file, property, io_exec, cpu_exec) -> any:
#         # NOTE: This function assumes that the file exists
        
#         # Get the path to the property file
#         p = self.__property_path(file, property)
        
#         # If the property file does not exist, generate it
#         if not p.exists():
#             return await self.__gen_property(file, property)
        
#         # Else, read the property file and return the data
#         return await read_file(p)
    
#     async def __gen_global_property(self, property, io_exec, cpu_exec):
#         # Make sure the property directory exists
#         p = self.__global_dir / property
#         os.makedirs(p.parent, exist_ok=True)
        
#         # Get the generator function
#         gen = self.__global_generators[property]
        
#         # Load the dependencies
#         deps = self.__load_dependencies(None, self.__global_dependencies[property])
        
#         # Generate the property
#         data = await gen(io_exec, cpu_exec)
        
#         # Write the data to the property file
#         await store_file(p, data)
        
#         # Return the data
#         return data

#     async def __fetch_global_property(self, property, io_exec, cpu_exec) -> any:
#         # Get the path to the property file
#         p = self.__global_dir / property
        
#         # If the property file does not exist, generate it
#         if not p.exists():
#             return await self.__gen_global_property(property)
        
#         # Else, read the property file and return the data
#         return await read_file(p)
    
#     def files(self, whitelist=None) -> list[Path]:
#         """List all files in the watch directory."""
#         if whitelist is None:
#             whitelist = [".txt", ".doc", ".docx", ".pdf", ".rtf", ".html"]
        
#         return [
#             path for path in self.__watch_dir.rglob("*")
#             if path.is_file() and path.suffix.lower() in (ext.lower() for ext in whitelist)
#         ]
    
    
#     async def preproc(self):
#         # Generate the text property
#         with 
        

#     # Overwrite the operator[]
#     def __getitem__(self, key : tuple[str, str]) -> any:
#         # Unpack the key
#         file, property = key
#         file = Path(file)
#         loop = asyncio.get_event_loop()
#         return loop.run_until_complete(self.__fetch_property(file, property))