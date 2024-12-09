from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from ezlib import EzManager


app = FastAPI(title="EzManager API", version="1.0.0")


# Initialize EzManager
WATCH_DIR = "data"
CACHE_DIR = "cache"
manager = EzManager(WATCH_DIR, CACHE_DIR)

# await manager.preproc_all()
manager.preproc_all_sync()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Match frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Preprocess Files
@app.post("/preprocess")
async def preprocess_files():
    """Preprocess all files in the watch directory."""
    try:
        await manager.preproc_all()
        return {"status": "success", "message": "Preprocessing completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Search Query Input Model
class SearchQuery(BaseModel):
    query: str
    threshold: Optional[int] = 80
    top_k: Optional[int] = 5
    use_fuzzy: Optional[bool] = True
    use_embeddings: Optional[bool] = True
    use_tfidf: Optional[bool] = True
    combine_results: Optional[bool] = True


# Search Files
@app.post("/search")
async def search_files(search_query: SearchQuery):
    """
    Search files using fuzzy matching, embeddings, and/or TF-IDF.
    """
    try:
        results = await manager.search(
            query=search_query.query,
            threshold=search_query.threshold,
            top_k=search_query.top_k,
            use_fuzzy=search_query.use_fuzzy,
            use_embeddings=search_query.use_embeddings,
            use_tfidf=search_query.use_tfidf,
            combine_results=search_query.combine_results,
        )
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# Similar Files Input Model
class SimilarFileQuery(BaseModel):
    file_path: str
    top_k: Optional[int] = 5


# Search Similar Files
@app.post("/search-similar")
async def search_similar_files(query: SimilarFileQuery):
    """
    Find similar files to a given file.
    """
    file_path = Path(query.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File {query.file_path} not found.")

    try:
        results = await manager.search_similar_files(file_path, top_k=query.top_k)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar files: {str(e)}")


# API Status
@app.get("/")
async def read_root():
    """Check the API status."""
    return {"status": "running", "message": "EzManager API is ready."}


# List all files
@app.get("/files")
async def list_files():
    """List all files in the watch directory."""
    try:
        files = [str(file) for file in manager.files()]
        return {"status": "success", "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


from fastapi.responses import FileResponse

@app.get("/view-pdf/{file_path}")
async def view_pdf(file_path: str):
    """
    Serve PDF files for viewing in the browser.
    """
    file_path = Path(WATCH_DIR).parent / file_path
    manager.logger.info(f"Viewing PDF file: {file_path}")
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Requested file is not a PDF.")
    return FileResponse(file_path, media_type="application/pdf")



# Run the API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
