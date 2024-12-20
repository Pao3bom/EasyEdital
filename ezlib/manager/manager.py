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
import re
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz, process
import numpy as np
from math import log
from sklearn.metrics.pairwise import cosine_similarity


def validate_word(word: any):
    # print(word)
    word = re.sub(r'[^\w0-9]+', '', word, flags=re.UNICODE)

    if len(word) == 0 or word.isnumeric():
        return False
    else:
        return True

def preproc_global_bag(global_bag : pd.DataFrame) -> pd.DataFrame:
    """Create the global keywords"""
    global_keywords = global_bag[global_bag["frequency"] >= 3]
    global_keywords = global_keywords[global_keywords['word'].apply(validate_word)]

    return global_keywords

def tfidf_stuff(indivual_bag : pd.DataFrame, global_bag : pd.DataFrame, corpus_size: int) -> pd.DataFrame:
    """Calculates the TF-IDF of a single file"""
    tfidf_df = indivual_bag.copy()
    tfidf_df["frequency"] = tfidf_df["word"].map(global_bag.set_index("word")["frequency"])
    # print('===== corupus size:', corpus_size)
    # print('>>>>>>>>>>>>>>>>>>>> tfidf_df:')
    # print(tfidf_df)
    
    # print('----------------- aaaaaa')
    tfidf_df["value"] = tfidf_df.apply(lambda row: row["count"] * log(corpus_size / row["frequency"]), axis=1)
    tfidf_df.drop(columns=["count", "frequency"], inplace=True)

    return tfidf_df

def log_exception(logger, message, exception):
    logger.error(f"{message}: {exception}", exc_info=True)

# Gets the value of a file using the TF-IDF
def tfdf_search_value(query: list[str], local_tfidf : pd.DataFrame) -> float:    
    # Fetch the TF-IDF values for the query words
    query_values = local_tfidf[local_tfidf["word"].isin(query)]["value"]
    
    # Calculate the sum of the TF-IDF values
    return query_values.sum().item()


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
        # model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_name='ulysses-camara/legal-bert-pt-br',
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
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),  # Logs to console
                logging.FileHandler("ezmanager.log", mode="a")  # Logs to a file
            ]
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

    async def load_global(self, property_name: str) -> str | pd.DataFrame | dict:
        """Load a global property from the cache."""
        try:
            global_path = self.__global_dir / property_name
            if "csv" in property_name:
                return pd.read_csv(global_path)
            if '.json' in property_name:
                async with aiofiles.open(global_path, "r") as f:
                    return json.loads(await f.read()) 
            async with aiofiles.open(global_path, "r") as f:
                return await f.read()
        except Exception as e:
            # self.logger.error(f"Failed to load global property '{property_name}': {e}")
            log_exception(self.logger, f"Failed to load global property '{property_name}'", e)
            raise e
        

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
            # self.logger.error(f"Failed to store property '{label}' for file {file}: {e}")
            log_exception(self.logger, f"Failed to store property '{label}' for file {file}", e)
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
            # self.logger.error(f"Failed to store global property '{label}': {e}")
            log_exception(self.logger, f"Failed to store global property '{label}'", e)
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
            # self.logger.error(f"Failed to write metadata for {file}: {e}")
            log_exception(self.logger, f"Failed to write metadata for {file}", e)
    
    
    
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
            # self.logger.error(f"Failed to generate embeddings for {file}: {e}")
            log_exception(self.logger, f"Failed to generate embeddings for {file}", e)
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
                # self.logger.error(error_msg)
                log_exception(self.logger, f"Failed to read embeddings for {file}", e)
                error_files.append({"file": str(file), "error": error_msg})

        # Save aggregated global embeddings
        try:
            global_path = self.__global_dir / "global_embeddings.json"
            async with aiofiles.open(global_path, "w") as f:
                await f.write(json.dumps(global_embeddings, indent=4))
            self.logger.info(f"Global embeddings saved to {global_path}.")
        except Exception as e:
            # self.logger.error(f"Failed to save global embeddings: {e}")
            log_exception(self.logger, "Failed to save global embeddings", e)
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
            # error_message = str(e)
            # self.logger.error(f"Error processing file {file}: {error_message}")
            log_exception(self.logger, f"Failed to process file {file}", e)

        finally:
            # Save metadata about the file
            await self.gen_metadata(file, parsing_success, is_scanned, error_message)
            
            
    async def process_file_2(self, file: Path, material, io_executor, cpu_executor: ProcessPoolExecutor):
        """
        Perform the second wave of processing for an individual file.
        - Applies the `tfidf_stuff` function using the global bag-of-words.
        - Saves the individual TF-IDF file.
        
        Args:
            file (Path): The path to the file to process.
            material (dict): Contains pre-loaded global data (e.g., global_bag).
            io_executor (ThreadPoolExecutor): Executor for IO-bound tasks.
            cpu_executor (ProcessPoolExecutor): Executor for CPU-bound tasks.
        """
        try:
            # Load individual bag-of-words
            bow_path = self.property_path(file, "bag_of_words.csv")
            if not bow_path.exists():
                self.logger.warning(f"Bag-of-words not found for {file}. Skipping.")
                return
            
            indiv_bag = await asyncio.to_thread(pd.read_csv, bow_path)

            # Retrieve global bag-of-words from material
            global_bag = material.get('global_bag')
            if global_bag is None:
                # self.logger.error("Global bag-of-words is missing. Skipping.")
                log_exception(self.logger, "Global bag-of-words is missing", None)
                return

            # Apply the `tfidf_stuff` function
            corpus_size = material.get('global_meta', {}).get('processed_files', 0)
            tfidf_result = await asyncio.to_thread(tfidf_stuff, indiv_bag, global_bag, corpus_size)

            # Save the resulting TF-IDF data
            tfidf_path = self.property_path(file, "tf-idf.csv")
            await asyncio.to_thread(tfidf_result.to_csv, tfidf_path, index=False)
            self.logger.info(f"TF-IDF saved for {file} at {tfidf_path}.")

        except Exception as e:
            # self.logger.error(f"Error in second wave processing for {file}: {e}")
            log_exception(self.logger, f"Failed to process file {file}", e)

    
    async def gen_global_bag_of_words(self):
        """
        Generate a global bag-of-words by combining individual bag-of-words.
        """
        self.logger.info("Generating global bag-of-words...")
        global_bow = pd.DataFrame(columns=["word", "count", "frequency"])
        error_files = []

        for file in self.files():
            try:
                bow_path = self.property_path(file, "bag_of_words.csv")
                if not bow_path.exists():
                    continue
                bow = pd.read_csv(bow_path)
                bow["frequency"] = 1
                global_bow = pd.concat([global_bow, bow]).groupby("word", as_index=False).sum()
            except Exception as e:
                error_files.append({"file": str(file), "error": str(e)})
                log_exception(self.logger, f"Failed to process bag-of-words for {file}", e)

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
        
        # td-df on global bag
        global_bag = await self.load_global("global_bag_of_words.csv")
        global_tfidf = await asyncio.to_thread(preproc_global_bag, global_bag)
        await self.store_global("global_tfidf.csv", global_tfidf)
        

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
        
        # Second wave of individual file processing
        material = {
            'global_bag': await self.load_global("global_bag_of_words.csv"),
            'global_meta': await self.load_global("global_meta.json"),
        }

        with ThreadPoolExecutor(max_workers=self.max_threads) as io_executor, \
            ProcessPoolExecutor(max_workers=self.max_processes) as cpu_executor:
            tasks = [self.process_file_2(file, material, io_executor, cpu_executor) for file in files]
            await self._with_progress_bar(tasks, self.total_files)

    # sync version of preproc_all
    def preproc_all_sync(self) -> None:
        """Synchronous wrapper for preproc_all."""
        asyncio.run(self.preproc_all())

    async def _with_progress_bar(self, tasks: list[asyncio.Task], total_files: int):
        """Wrap tasks with a progress bar for feedback."""
        await async_tqdm.gather(*tasks, desc="Processing Files", total=total_files, unit="files")


    async def fuzzy_search_text(self, query: str, threshold : int | None = None) -> list[dict]:
        """
        Perform fuzzy search on cached text transcripts, matching by path, file name, or file contents.
        
        Args:
            query (str): The search query.
            threshold (int): Minimum similarity score to include in the results.

        Returns:
            list[dict]: A list of matches with their file paths, names, and scores.
        """
        results = []

        for file in self.files():
            try:
                # Get cached text
                text = await self.get_text(file)
                file_name_score = fuzz.partial_ratio(query, file.name)
                file_path_score = fuzz.partial_ratio(query, str(file))
                content_score = fuzz.partial_ratio(query, text)

                # Aggregate scores
                if threshold is not None and max(file_name_score, file_path_score, content_score) >= threshold:
                    results.append({
                        "file_path": str(file),
                        "file_name": file.name,
                        "file_path_score": file_path_score,
                        "file_name_score": file_name_score,
                        "content_score": content_score,
                        "max_score": max(file_path_score, file_name_score, content_score),
                        "mean_score": (file_path_score + file_name_score + content_score) / 3,
                    })
                
            except Exception as e:
                log_exception(self.logger, f"Failed to search file {file}", e)
        
        return sorted(results, key=lambda x: max(x["file_path_score"], x["file_name_score"], x["content_score"]), reverse=True)


    async def search_using_tfidf(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Perform search using TF-IDF values.
        
        Args:
            query (str): The search query.
            top_k (int): Number of top results to return.

        Returns:
            list[dict]: A list of matches with their file paths, names, and scores.
        """

        # Load global TF-IDF data
        global_tfidf = await self.load_global("global_tfidf.csv")

        # Preprocess the query
        query = query.lower().split()
        query = [word for word in query if word in global_tfidf["word"].values]

        # Calculate search values
        results = []
        for file in self.files():
            try:
                # load individual TF-IDF data
                tfidf_path = self.property_path(file, "tf-idf.csv")
                
                if not tfidf_path.exists():
                    self.logger.warning(f"TF-IDF data not found for {file}. Skipping.")
                    continue
                
                tfidf = pd.read_csv(tfidf_path)
            
                score = tfdf_search_value(query, tfidf)
                results.append({
                    "file_path": str(file),
                    "file_name": file.name,
                    "search_value": score,
                })
            except Exception as e:
                log_exception(self.logger, f"Failed to search file {file}", e)

        return sorted(results, key=lambda x: x["search_value"], reverse=True)[:top_k]


    async def search_similar_files(self, basefile: str, top_k: int = 5) -> list[dict]:
        """
        Perform semantic search using cached embeddings against a given file.
        
        Args:
            file (str): The file path.
            top_k (int): Number of top results to return.

        Returns:
            list[dict]: A list of matches with their file paths, names, and similarity scores.
        """
        base_embed_path = self.property_path(basefile, "embeddings.json")

        async with aiofiles.open(base_embed_path, "r") as f:
            base_embedding = np.array(json.loads(await f.read())) 
            base_embedding = base_embedding.reshape(1, -1)

        matches = []
        
        for file in self.files():
            if file == basefile:
                continue

            try:
                # Load cached embeddings
                embed_path = self.property_path(file, "embeddings.json")
                if not embed_path.exists():
                    self.logger.warning(f"Embeddings not found for {file}. Skipping.")
                    continue
                
                async with aiofiles.open(embed_path, "r") as f:
                    file_embedding = np.array(json.loads(await f.read()))

                # Calculate similarity
                similarity_score = cosine_similarity(base_embedding, file_embedding.reshape(1, -1)).item()
                matches.append({
                    "file_path": str(file),
                    "file_name": file.name,
                    "similarity_score": similarity_score,
                })
            except Exception as e:
                log_exception(self.logger, f"Failed to perform embedding search for {file}", e)

        return sorted(matches, key=lambda x: x["similarity_score"], reverse=True)[:top_k]
    
    async def search_using_embeddings(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Perform semantic search using cached embeddings.
        
        Args:
            query (str): The search query.
            top_k (int): Number of top results to return.

        Returns:
            list[dict]: A list of matches with their file paths, names, and similarity scores.
        """
        query_embedding = self.model.encode(query.lower(), device="cuda" if torch.cuda.is_available() else "cpu")
        query_embedding = query_embedding.reshape(1, -1)  # Reshape for cosine similarity calculation

        matches = []
        
        for file in self.files():
            try:
                # Load cached embeddings
                embed_path = self.property_path(file, "embeddings.json")
                if not embed_path.exists():
                    self.logger.warning(f"Embeddings not found for {file}. Skipping.")
                    continue
                
                async with aiofiles.open(embed_path, "r") as f:
                    file_embedding = np.array(json.loads(await f.read()))

                # Calculate similarity
                similarity_score = cosine_similarity(query_embedding, file_embedding.reshape(1, -1)).item()
                matches.append({
                    "file_path": str(file),
                    "file_name": file.name,
                    "similarity_score": similarity_score,
                })
            except Exception as e:
                log_exception(self.logger, f"Failed to perform embedding search for {file}", e)

        return sorted(matches, key=lambda x: x["similarity_score"], reverse=True)[:top_k]

    
    async def search(
        self,
        query: str,
        threshold: int = 80,
        top_k: int = 5,
        use_fuzzy: bool = True,
        use_embeddings: bool = True,
        use_tfidf: bool = True,
        combine_results: bool = True
    ) -> dict:
        """
        Perform a combined search using fuzzy matching, embeddings, and TF-IDF.

        Args:
            query (str): The search query.
            threshold (int): Minimum similarity score for fuzzy search results.
            top_k (int): Number of top results to return from each method.
            use_fuzzy (bool): Whether to include fuzzy search in the results.
            use_embeddings (bool): Whether to include embedding-based search in the results.
            use_tfidf (bool): Whether to include TF-IDF search in the results.
            combine_results (bool): Whether to combine the results from different methods.

        Returns:
            dict: A dictionary containing results from each method and combined results if applicable.
        """
        results = {}
        combined_results = []
        methods = []

        if use_fuzzy:
            self.logger.info("Performing fuzzy search...")
            fuzzy_results = await self.fuzzy_search_text(query, threshold=threshold)
            for res in fuzzy_results:
                res["type"] = "fuzzy"
                res["relevance"] = max(res["file_path_score"], res["file_name_score"], res["content_score"])
            results["fuzzy"] = fuzzy_results[:top_k]
            methods.append("fuzzy")

        if use_embeddings:
            self.logger.info("Performing semantic search using embeddings...")
            embed_results = await self.search_using_embeddings(query, top_k=top_k)
            for res in embed_results:
                res["type"] = "embedding"
                res["relevance"] = res["similarity_score"]
            results["embedding"] = embed_results
            methods.append("embedding")

        if use_tfidf:
            self.logger.info("Performing TF-IDF search...")
            tfidf_results = await self.search_using_tfidf(query, top_k=top_k)
            for res in tfidf_results:
                res["type"] = "tfidf"
                res["relevance"] = res["search_value"]
            results["tfidf"] = tfidf_results
            methods.append("tfidf")

        if combine_results:
            # Combine results from different methods
            combined = {}
            for method in methods:
                for res in results[method]:
                    key = res["file_path"]
                    if key not in combined:
                        combined[key] = {
                            "file_path": res["file_path"],
                            "file_name": res["file_name"],
                            "types": [method],
                            "relevance_scores": {method: res["relevance"]}
                        }
                    else:
                        combined[key]["types"].append(method)
                        combined[key]["relevance_scores"][method] = res["relevance"]

            # Calculate combined relevance (e.g., average of relevance scores)
            for res in combined.values():
                # You can adjust the weighting here if needed
                res["relevance"] = sum(res["relevance_scores"].values()) / len(res["relevance_scores"])
                combined_results.append(res)

            # Sort combined results
            combined_results = sorted(combined_results, key=lambda x: x["relevance"], reverse=True)[:top_k]
            results["combined"] = combined_results

        return results

