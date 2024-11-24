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


class EzManager:
    def __init__(self, watch_dir: str | Path, cache_dir: str | Path):
        self.__watch_dir = Path(watch_dir)
        self.__cache_dir = Path(cache_dir)
        
        # Create the cache structure
        os.makedirs(self.__cache_dir / "global", exist_ok=True)
        os.makedirs(self.__cache_dir / "files", exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("EzManager")

    # Iterator for all files in the watch directory
    def files(self) -> list[Path]:
        """List all files in the watch directory."""
        return [path for path in self.__watch_dir.rglob("*") if path.is_file()]

    async def preproc_all(self) -> None:
        """Preprocess all files in the watch directory concurrently with progress feedback."""
        async def process_file(file: Path, low_executor, high_executor: ProcessPoolExecutor):
            """Process a single file."""
            try:
                content = await self.get_text(file, high_executor)
                await self.gen_bag_of_words(file, content, low_executor)
            except Exception as e:
                self.logger.error(f"Error processing file {file}: {e}")
                raise e

        files = self.files()
        self.total_files = len(files)

        if self.total_files == 0:
            self.logger.info("No files to process.")
            return

        with ThreadPoolExecutor() as low_executor, ProcessPoolExecutor() as high_executor:
            # Use TQDM for progress bar
            tasks = [
                process_file(file, low_executor, high_executor) for file in files
            ]
            # Wrap tasks with a TQDM progress bar
            await async_tqdm.gather(*tasks, desc="Processing Files", total=self.total_files)

    def preprocess(self) -> None:
        """Synchronous wrapper for preproc_all."""
        asyncio.run(self.preproc_all())

    def file_path_on_cache(self, file: Path) -> Path:
        """Get the cache path for a given file."""
        return self.__cache_dir / "files" / file.relative_to(self.__watch_dir)

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
            raise

    async def gen_text(self, file: Path, executor: ProcessPoolExecutor = None, force: bool = False) -> str | None:
        """Parse the text content of a file and store it in the cache."""
        property_path = self.property_path(file, "text")
        if not force and property_path.exists():
            return None

        text = await hard_parse(file, executor)
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
        words = await loop.run_in_executor(executor, lambda: pd.DataFrame(count_words(content).items(), columns=["word", "count"]))
        await loop.run_in_executor(None, words.to_csv, property_path, False)

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
