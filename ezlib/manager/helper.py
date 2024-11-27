import os
import asyncio
import aiofiles
import pandas as pd
from pathlib import Path
import json


def calculate_limits(max_threads : int | None = None, max_processes : int | None = None):
    """Calculate reasonable limits for threads and processes."""
    max_threads = max_threads or min(32, os.cpu_count() * 2)
    max_processes = max_processes or min(16, os.cpu_count())
    return max_threads, max_processes
    



async def store_csv(file_path: Path, content: dict) -> None:
    """Store the content in a CSV file."""
    df = pd.DataFrame(content)
    await asyncio.to_thread(df.to_csv, file_path, index=False)


async def store_json(file_path: Path, content: dict) -> None:
    """Store the content in a JSON file."""
    async with aiofiles.open(file_path, mode='w') as f:
        await f.write(json.dumps(content))


async def store_text(file_path: Path, content: str) -> None:
    """Store the content in a text file."""
    async with aiofiles.open(file_path, mode='w') as f:
        await f.write(content)


async def store_file(file_path: Path, content: any) -> None:
    """Store the content in the file."""
    extension = file_path.suffix
    
    match extension:
        case '.csv':    await store_csv(file_path, content)
        case '.json':   await store_json(file_path, content)
        case '.txt':    await store_text(file_path, content)
        
        case _: raise ValueError(f"Unsupported file extension: {extension}")





async def read_csv(file_path: Path) -> pd.DataFrame:
    """Read the content from a CSV file."""
    return await asyncio.to_thread(pd.read_csv, file_path)


async def read_json(file_path: Path) -> dict:
    """Read the content from a JSON file."""
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
        return json.loads(content)


async def read_text(file_path: Path) -> str:
    """Read the content from a text file."""
    async with aiofiles.open(file_path, mode='r') as f:
        return await f.read()


async def read_file(file_path: Path) -> any:
    """Read the content from the file."""
    extension = file_path.suffix
    
    match extension:
        case '.csv':    return await read_csv(file_path)
        case '.json':   return await read_json(file_path)
        case '.txt':    return await read_text(file_path)
        
        case _: raise ValueError(f"Unsupported file extension: {extension}")





async def with_progress_bar(tasks: list[asyncio.Task], total_files: int):
        """Wrap tasks with a progress bar for feedback."""
        await async_tqdm.gather(*tasks, desc="Processing Files", total=total_files, unit="files")
        
        
        
        
with ThreadPoolExecutor(max_workers=self.max_threads) as io_executor, \
             ProcessPoolExecutor(max_workers=self.max_processes) as cpu_executor:
            tasks = [self.process_file_1(file, io_executor, cpu_executor) for file in files]
            await self._with_progress_bar(tasks, self.total_files)