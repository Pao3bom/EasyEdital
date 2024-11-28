from ezlib import EzManager
import asyncio
from pathlib import Path

def print_results(title, results):
    """Helper function to display search results neatly."""
    print("\n" + "=" * 50)
    print(title)
    if results:
        for res in results:
            print(f"File: {res['file_name']}")
            print(f"Path: {res['file_path']}")
            if "relevance" in res:
                print(f"Relevance: {res['relevance']:.4f}")
            if "similarity_score" in res:
                print(f"Similarity Score: {res['similarity_score']:.4f}")
            if "search_value" in res:
                print(f"TF-IDF Score: {res['search_value']:.4f}")
            if "file_name_score" in res:
                print(f"File Name Score: {res['file_name_score']}")
            if "file_path_score" in res:
                print(f"File Path Score: {res['file_path_score']}")
            if "content_score" in res:
                print(f"Content Score: {res['content_score']}")
            if "types" in res:
                print(f"Matched Methods: {', '.join(res['types'])}")
            print("-" * 50)
    else:
        print("No results found.")
    print("=" * 50)

async def run_demo():
    """Run the EzManager demo."""
    print('\n' + '=' * 50)
    print("Running EzManager Demonstration")

    # Initialize the EzManager with sample directories
    watch_dir = "data"
    cache_dir = "cache"
    manager = EzManager(watch_dir, cache_dir)

    # Preprocess the files
    print("Preprocessing files...")
    await manager.preproc_all()
    print("Preprocessing complete.")

    # Ask if results should be combined
    combine_results = input("\nDo you want to combine the results from all methods? (yes/no): ").strip().lower() == "yes"

    # Perform a search using all methods
    query = input("\nEnter a search query: ")
    search_results = await manager.search(query, use_fuzzy=True, use_embeddings=True, use_tfidf=True, combine_results=combine_results)

    # Display results
    if combine_results:
        print_results("Combined Search Results", search_results.get("combined", []))
    else:
        print_results("Fuzzy Search Results", search_results.get("fuzzy", []))
        print_results("Embedding Search Results", search_results.get("embedding", []))
        print_results("TF-IDF Search Results", search_results.get("tfidf", []))

    # Perform a similar files search
    new_file_path = input("\nEnter the path to a new file to find similar files: ").strip()
    if Path(new_file_path).is_file():
        similar_files = await manager.search_similar_files(Path(new_file_path))
        print_results("Similar Files Results", similar_files)
    else:
        print(f"The file {new_file_path} does not exist or is invalid.")

def main():
    asyncio.run(run_demo())

if __name__ == "__main__":
    main()
