import os
from pathlib import Path
import asyncio
import aiofiles
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from tqdm.asyncio import tqdm as async_tqdm  # For progress bars with asyncio
from ..parser import hard_parse, is_scanned_pdf
from ..keyword import count_words
import pandas as pd
import logging
import psutil  # For dynamic system load monitoring
import json
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer


class EzManager:
    """
    EzManager: A manager class for preprocessing files in a directory.
    
    Features:
    - Parse text from various file types and cache it.
    - Generate bag-of-words representations and cache them.
    - Handle asynchronous processing with progress feedback.
    - Perform global file processing tasks.
    - Maintain a structured cache for processed properties.
    """
    def __init__(
        self, 
        watch_dir: str | Path, 
        cache_dir: str | Path, 
        max_threads=None, 
        max_processes=None, 
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ) -> None:
        self.__watch_dir = Path(watch_dir)
        self.__cache_dir = Path(cache_dir)
        
        self.__temp_dir = self.__cache_dir / "temp"
        self.__files_dir = self.__cache_dir / "files"
        self.__global_dir = self.__cache_dir / "global"
        
        # Create the cache structure
        os.makedirs(self.__global_dir, exist_ok=True)
        os.makedirs(self.__files_dir, exist_ok=True)
        os.makedirs(self.__temp_dir, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("EzManager")

        # Set worker limits
        self.max_threads, self.max_processes = self.calculate_limits(max_threads, max_processes)
        
        # Initialize the embedding model
        self.model = SentenceTransformer(model_name, device="cuda" if torch.cuda.is_available() else "cpu")

    def calculate_limits(self, max_threads, max_processes):
        """Calculate reasonable limits for threads and processes."""
        max_threads = max_threads or min(32, os.cpu_count() * 2)
        max_processes = max_processes or min(16, os.cpu_count())
        return max_threads, max_processes

    def files(self, whitelist=None) -> list[Path]:
        """List all files in the watch directory."""
        if whitelist is None:
            whitelist = [".txt", ".doc", ".docx", ".pdf", ".rtf", ".html"]
        
        return [
            path for path in self.__watch_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in (ext.lower() for ext in whitelist)
        ]

    def preprocess(self) -> None:
        """Synchronous wrapper for preproc_all."""
        asyncio.run(self.preproc_all())

    def file_path_on_cache(self, file: Path) -> Path:
        """Get the cache path for a given file."""
        return self.__files_dir / file.relative_to(self.__watch_dir)

    def property_path(self, file: Path, label: str) -> Path:
        """Get the path to store a specific property for a file in the cache."""
        return self.file_path_on_cache(file) / label

    async def store(self, file: Path, label: str, content: str, mode: str = "w") -> None:
        """Store a property for a file in the cache."""
        try:
            cache_path = self.file_path_on_cache(file)
            os.makedirs(cache_path, exist_ok=True)
            async with aiofiles.open(self.property_path(file, label), mode) as f:
                await f.write(content)
        except Exception as e:
            self.logger.error(f"Failed to store property '{label}' for file {file}: {e}")
            raise e

    async def store_global(self, label: str, content: str | pd.DataFrame, mode: str = "w") -> None:
        """Store a global property."""
        try:
            global_path = self.__global_dir / label
            if isinstance(content, pd.DataFrame):
                content.to_csv(global_path, index=False)
            else:
                async with aiofiles.open(global_path, mode) as f:
                    await f.write(content)
        except Exception as e:
            self.logger.error(f"Failed to store global property '{label}': {e}")
            raise e

    async def gen_text(self, file: Path, executor: ProcessPoolExecutor = None, force: bool = False) -> str | None:
        """Parse the text content of a file and store it in the cache."""
        property_path = self.property_path(file, "text")
        if not force and property_path.exists():
            return None

        text = await hard_parse(file, executor, temp_dir=self.__temp_dir)
        await self.store(file, "text", text)
        return text

    async def get_text(self, file: Path, executor: ProcessPoolExecutor = None, force: bool = False) -> str:
        """Get the parsed text content of a file from the cache or parse it."""
        text = await self.gen_text(file, executor, force)
        if text is None:
            async with aiofiles.open(self.property_path(file, "text"), "r") as f:
                return await f.read()
        return text

    async def gen_bag_of_words(self, file: Path, content: str = None, executor: ProcessPoolExecutor = None, force: bool = False) -> None:
        """Generate the bag of words for a file and store it in the cache."""
        property_path = self.property_path(file, "bag_of_words.csv")
        if not force and property_path.exists():
            return

        content = content or await self.get_text(file, executor)
        loop = asyncio.get_running_loop()
        words = await loop.run_in_executor(
            executor,
            lambda: pd.DataFrame(count_words(content).items(), columns=["word", "count"])
        )
        await loop.run_in_executor(None, lambda: words.to_csv(property_path, index=False))

    async def get_bag_of_words(self, file: Path, executor: ProcessPoolExecutor = None, force: bool = False) -> pd.DataFrame:
        """Retrieve the bag of words for a file from the cache or generate it."""
        await self.gen_bag_of_words(file, executor=executor, force=force)
        property_path = self.property_path(file, "bag_of_words.csv")
        return pd.read_csv(property_path)

    async def gen_metadata(self, file: Path, parsing_success: bool, is_scanned: bool, error_message: str = None):
        """Generate and store metadata about the file."""
        meta_data = {
            "file_name": file.name,
            "file_path": str(file),
            "parsing_success": parsing_success,
            "is_scanned_pdf": is_scanned,
            "error_message": error_message,
            "processing_time": datetime.now().isoformat(),
        }
        try:
            meta_path = self.property_path(file, "meta.json")
            async with aiofiles.open(meta_path, "w") as meta_file:
                await meta_file.write(json.dumps(meta_data, indent=4))
        except Exception as e:
            self.logger.error(f"Failed to write metadata for {file}: {e}")
            
            
    async def gen_embeddings(self, file: Path, content = None, force: bool = False) -> None:
        """
        Generate embeddings for a file and store them in the cache.
        """
        property_path = self.property_path(file, "embeddings.json")
        if not force and property_path.exists():
            return
        
        if content is None:
            content = await self.get_text(file)

        try:
            # Generate embeddings
            embeddings = self.model.encode(content.lower(), device="cuda" if torch.cuda.is_available() else "cpu")
            embeddings = embeddings.tolist()  # Convert to list for JSON serialization

            # Save embeddings
            async with aiofiles.open(property_path, "w") as f:
                await f.write(json.dumps(embeddings))
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings for {file}: {e}")
            raise e

    async def gen_global_embeddings(self) -> list[dict]:
        """
        Aggregate embeddings for all files into a single global JSON file.
        
        Returns:
            error_files (list[dict]): List of files with errors during embedding aggregation.
        """
        self.logger.info("Generating global embeddings...")
        global_embeddings = {}
        error_files = []

        for file in self.files():
            try:
                # Check if embeddings for the file exist
                property_path = self.property_path(file, "embeddings.json")
                if not property_path.exists():
                    self.logger.warning(f"Embeddings not found for {file}. Skipping.")
                    continue

                # Read embeddings from the cache
                async with aiofiles.open(property_path, "r") as f:
                    embeddings = await f.read()
                    global_embeddings[file.name] = json.loads(embeddings)
            except Exception as e:
                error_msg = f"Failed to read embeddings for {file}: {e}"
                self.logger.error(error_msg)
                error_files.append({"file": str(file), "error": error_msg})

        # Save aggregated global embeddings
        try:
            global_path = self.__global_dir / "global_embeddings.json"
            async with aiofiles.open(global_path, "w") as f:
                await f.write(json.dumps(global_embeddings, indent=4))
            self.logger.info(f"Global embeddings saved to {global_path}.")
        except Exception as e:
            self.logger.error(f"Failed to save global embeddings: {e}")
            raise e

        return error_files


    async def process_file_1(self, file: Path, io_executor, cpu_executor: ProcessPoolExecutor):
        """Process a single file by generating its text, bag-of-words, and metadata."""
        error_message = None
        parsing_success = False
        is_scanned = False
        try:
            # Parse text content
            content = await self.get_text(file, cpu_executor)
            parsing_success = bool(content and not content.isspace())
            is_scanned = is_scanned_pdf(file, content)
            
            if parsing_success:
                # Generate bag-of-words
                await self.gen_bag_of_words(file, content, io_executor)
                
                # Generate embeddings
                await self.gen_embeddings(file, content)

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Error processing file {file}: {error_message}")

        finally:
            # Save metadata about the file
            await self.gen_metadata(file, parsing_success, is_scanned, error_message)

    async def gen_global_bag_of_words(self):
        """
        Generate a global bag-of-words by combining individual bag-of-words.
        """
        self.logger.info("Generating global bag-of-words...")
        global_bow = pd.DataFrame(columns=["word", "count"])
        error_files = []

        for file in self.files():
            try:
                bow_path = self.property_path(file, "bag_of_words.csv")
                if not bow_path.exists():
                    continue
                bow = pd.read_csv(bow_path)
                global_bow = pd.concat([global_bow, bow]).groupby("word", as_index=False).sum()
            except Exception as e:
                self.logger.error(f"Failed to process bag-of-words for {file}: {e}")
                error_files.append({"file": str(file), "error": str(e)})

        # Save global bag-of-words
        await self.store_global("global_bag_of_words.csv", global_bow)

        return error_files

    async def gen_global_metadata(self, error_files):
        """
        Generate global metadata summarizing the processing results.
        """
        self.logger.info("Generating global metadata...")
        global_meta = {
            "total_files": self.total_files,
            "processed_files": self.total_files - len(error_files),
            "failed_files": len(error_files),
            "errors": error_files,
            "processing_time": datetime.now().isoformat(),
        }

        await self.store_global("global_meta.json", json.dumps(global_meta, indent=4))

    async def global_processing(self):
        """
        Perform all global processing tasks:
        - Generate global bag-of-words.
        - Generate global embeddings.
        - Generate global metadata.
        """
        # Generate global bag-of-words and collect errors
        bow_error_files = await self.gen_global_bag_of_words()

        # Generate global embeddings and collect errors
        embed_error_files = await self.gen_global_embeddings()

        # Combine errors from all global tasks
        all_errors = bow_error_files + embed_error_files

        # Generate global metadata
        await self.gen_global_metadata(all_errors)

    async def preproc_all(self) -> None:
        """Preprocess all files and perform global processing."""
        files = self.files()
        self.total_files = len(files)

        if self.total_files == 0:
            self.logger.info("No files to process.")
            return

        self.logger.info(f"Processing {self.total_files} files from {self.__watch_dir}.")
        self.logger.info(f"Using {self.max_threads} threads and {self.max_processes} processes.")
        
        # First wave of individual file processing
        with ThreadPoolExecutor(max_workers=self.max_threads) as io_executor, \
             ProcessPoolExecutor(max_workers=self.max_processes) as cpu_executor:
            tasks = [self.process_file_1(file, io_executor, cpu_executor) for file in files]
            await self._with_progress_bar(tasks, self.total_files)
        
        # First wave of global processing
        await self.global_processing()

    async def _with_progress_bar(self, tasks: list[asyncio.Task], total_files: int):
        """Wrap tasks with a progress bar for feedback."""
        await async_tqdm.gather(*tasks, desc="Processing Files", total=total_files, unit="files")
