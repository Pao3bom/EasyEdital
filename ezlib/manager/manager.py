import os
from pathlib import Path
import asyncio
import aiofiles
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from tqdm.asyncio import tqdm as async_tqdm  # For progress bars with asyncio
from ..parser import hard_parse
from ..keyword import count_words
import pandas as pd
import logging
import psutil  # For dynamic system load monitoring


class EzManager:
    """
    EzManager: A manager class for preprocessing files in a directory.
    
    Features:
    - Parse text from various file types and cache it.
    - Generate bag-of-words representations and cache them.
    - Handle asynchronous processing with progress feedback.
    - Maintain a structured cache for processed properties.
    """
    def __init__(self, watch_dir: str | Path, cache_dir: str | Path, max_threads=None, max_processes=None):
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

    def calculate_limits(self, max_threads, max_processes):
        """Calculate reasonable limits for threads and processes."""
        # Use defaults if not provided
        max_threads = max_threads or min(32, os.cpu_count() * 2)
        max_processes = max_processes or min(16, os.cpu_count())

        # Optionally adjust based on system load
        # load = psutil.cpu_percent()
        # if load > 80:  # Example logic for high system load
        #     max_threads = max(4, os.cpu_count())  # Reduce threads for IO
        #     max_processes = max(2, os.cpu_count() // 2)  # Reduce processes for CPU

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

    def __getitem__(self, key: tuple[str | Path, str]) -> str | pd.DataFrame:
        """Get a specific property for a file."""
        file, property = key
        match property:
            case "text":
                return asyncio.run(self.get_text(Path(file)))
            case "bag_of_words":
                return asyncio.run(self.get_bag_of_words(Path(file)))
            case _:
                raise KeyError(f"Unknown property: {property}")

    async def preproc_all(self) -> None:
        """
        Preprocess all files in the watch directory concurrently.

        Tasks:
        - Parse text from each file and cache it.
        - Generate a bag-of-words representation and cache it.
        - Provide progress feedback using a TQDM progress bar.
        """
        async def process_file(file: Path, io_executor, cpu_executor: ProcessPoolExecutor):
            """Process a single file by generating its text and bag-of-words."""
            try:
                # Parse text and generate bag-of-words
                content = await self.get_text(file, cpu_executor)
                await self.gen_bag_of_words(file, content, io_executor)
            except Exception as e:
                self.logger.error(f"Error processing file {file}: {e}")

        files = self.files()
        self.total_files = len(files)

        if self.total_files == 0:
            self.logger.info("No files to process.")
            return

        # Log the number of files to be processed
        self.logger.info(f"Processing {self.total_files} files from {self.__watch_dir}.")
        
        # Log the worker limits
        self.logger.info(f"Using {self.max_threads} threads and {self.max_processes} processes.")

        with ThreadPoolExecutor(max_workers=self.max_threads) as io_executor, \
             ProcessPoolExecutor(max_workers=self.max_processes) as cpu_executor:
            tasks = [process_file(file, io_executor, cpu_executor) for file in files]
            await self._with_progress_bar(tasks, self.total_files)

    async def _with_progress_bar(self, tasks: list[asyncio.Task], total_files: int):
        """Wrap tasks with a progress bar for feedback."""
        await async_tqdm.gather(*tasks, desc="Processing Files", total=total_files, unit="files")
