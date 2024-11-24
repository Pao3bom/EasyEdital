from typing import Callable, List
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio

# File reading and writing functions remain unchanged
async def read_file(filepath: str) -> str:
    loop = asyncio.get_event_loop()
    with open(filepath, 'r') as f:
        return await loop.run_in_executor(None, f.read)

async def write_file(filepath: str, content: str):
    loop = asyncio.get_event_loop()
    with open(filepath, 'w') as f:
        await loop.run_in_executor(None, f.write, content)

# Function to handle multiple CPU-bound tasks for a single input file
async def preprocess_file_multiple_tasks(
    input_path: str,
    output_paths: List[str],
    tasks: List[Callable[[str], str]],
    executor
):
    """
    Process a single input file using multiple tasks, and write to corresponding output files.
    
    Args:
        input_path (str): Path to the input file.
        output_paths (List[str]): List of output file paths, one for each task.
        tasks (List[Callable[[str], str]]): List of functions to apply to the input content.
        executor: Executor for CPU-bound tasks.
    """
    # Read the input file
    content = await read_file(input_path)

    # Process the file content using multiple tasks concurrently
    loop = asyncio.get_event_loop()
    processed_contents = await asyncio.gather(
        *[
            loop.run_in_executor(executor, task, content)
            for task in tasks
        ]
    )

    # Write each processed result to its corresponding output file
    await asyncio.gather(
        *[
            write_file(output_path, processed_content)
            for output_path, processed_content in zip(output_paths, processed_contents)
        ]
    )

# Function to process multiple files with multiple tasks
async def preprocess_files_multiple_tasks(
    files: List[Tuple[str, List[str]]],
    tasks: List[Callable[[str], str]],
    max_threads: int = 4
):
    """
    Process multiple files using multiple tasks, and write to corresponding output files.

    Args:
        files (List[Tuple[str, List[str]]]): List of input file paths and corresponding lists of output paths.
        tasks (List[Callable[[str], str]]): List of functions to apply to the input content.
        max_threads (int): Maximum number of threads for I/O-bound tasks.
    """
    with ThreadPoolExecutor(max_threads) as io_executor, ProcessPoolExecutor(max_threads) as cpu_executor:
        await asyncio.gather(
            *[
                preprocess_file_multiple_tasks(input_path, output_paths, tasks, cpu_executor)
                for input_path, output_paths in files
            ]
        )
