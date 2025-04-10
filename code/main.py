# # main.py
# import os
# import pandas as pd
# from fastapi import FastAPI, Query
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# import numpy as np
# from config import *
# from utility import *

# # Initialize FastAPI
# app = FastAPI()

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Serve static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Global variables
# df = None
# faiss_index = None
# embeddings = None
# model = None

# def initialize_system():
#     """Run the full processing pipeline"""
#     global df, faiss_index, embeddings, model
    
#     print("🚀 Starting resume processing pipeline...")
    
#     # Step 1: Extract text from PDFs
#     if not os.path.exists(EXTRACTED_DATA):
#         print("🔍 Extracting text from resumes...")
#         resume_data = []
        
#         for category in os.listdir(BASE_DIR):
#             category_path = os.path.join(BASE_DIR, category)
#             if os.path.isdir(category_path): 
#                 for file in os.listdir(category_path):
#                     if file.endswith(".pdf"):
#                         pdf_path = os.path.join(category_path, file)
#                         text = extract_text(pdf_path)
#                         resume_data.append([file, category, text])
        
#         df = pd.DataFrame(resume_data, columns=["Filename", "Category", "Extracted_Text"])
#         df.to_csv(EXTRACTED_DATA, index=False)
#         print(f"✅ Extracted {len(df)} resumes to {EXTRACTED_DATA}")
#     else:
#         df = pd.read_csv(EXTRACTED_DATA)
#         print(f"📄 Using existing extracted data: {EXTRACTED_DATA}")

#     # Step 2: Clean and process text
#     if not os.path.exists(CLEANED_DATA):
#         print("🧹 Cleaning resume text...")
#         process_resumes(EXTRACTED_DATA, CLEANED_DATA)
#     else:
#         print(f"📄 Using existing cleaned data: {CLEANED_DATA}")
    
#     df = pd.read_csv(CLEANED_DATA)

#     # Step 3: Generate embeddings
#     if not os.path.exists(EMBEDDINGS_PATH):
#         print("🔢 Generating embeddings...")
#         generate_embeddings(CLEANED_DATA, EMBEDDINGS_PATH)
#     else:
#         print(f"📄 Using existing embeddings: {EMBEDDINGS_PATH}")

#     # Step 4: Build FAISS index
#     if not os.path.exists(FAISS_INDEX_FILE):
#         print("🏗️ Building FAISS index...")
#         build_faiss_index(EMBEDDINGS_PATH, FAISS_INDEX_FILE)
#     else:
#         print(f"📄 Using existing FAISS index: {FAISS_INDEX_FILE}")

#     # Load model and index
#     print("⚙️ Loading model and index...")
#     model = SentenceTransformer(MODEL_NAME)
#     faiss_index, embeddings = load_faiss_index(FAISS_INDEX_FILE, EMBEDDINGS_PATH)
    
#     print("🎉 System ready!")

# # API Endpoints

# @app.get("/search")
# async def search(job_description: str = Query(..., description="Job description to search")):
#     """Search resumes based on job description"""
#     if not job_description:
#         return {"error": "Job description cannot be empty"}
    
#     # Convert query to embedding
#     query_embedding = model.encode([job_description], convert_to_tensor=False)[0].astype("float32")
    
#     # Search FAISS index
#     distances, indices = faiss_index.search(np.array([query_embedding]), k=5)
    
#     # Prepare results
#     results = [] 
#     for i, idx in enumerate(indices[0]):
#         if idx < len(df):
#             results.append({
#                 "filename": df.iloc[idx]["Filename"],
#                 "category": df.iloc[idx]["Category"],
#                 "text": df.iloc[idx]["Cleaned_Text"],
#                 "score": abs((float(1 - distances[0][i]))*100),  # Convert to float for JSON
#                 "file_path": f"/pdfs/{df.iloc[idx]['Filename']}"

#             })
    
#     return {"query": job_description, "results": results[::-1]}

# # Replace the get_pdf endpoint with this version
# @app.get("/pdfs/{filename}")
# async def get_pdf(filename: str):
#     """Serve PDF files with proper path handling"""
#     try:
#         file_path = find_pdf(filename)
#         if not file_path or not os.path.exists(file_path):
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"PDF not found: {filename}"
#             )
        
#         # Verify it's a PDF file
#         if not file_path.lower().endswith('.pdf'):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Requested file is not a PDF"
#             )
            
#         return FileResponse(
#             file_path,
#             media_type='application/pdf',
#             headers={'Content-Disposition': f'inline; filename="{filename}"'}
#         )
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error serving PDF: {str(e)}"
#         )

# # Initialize the system when starting
# initialize_system()

import os
import numpy as np
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sentence_transformers import SentenceTransformer
from dbutils import get_db_connection
from utility import find_pdf
from numpy.linalg import norm

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (e.g., frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load model once on startup
model = SentenceTransformer("all-MiniLM-L6-v2")


@app.get("/search")
async def search(job_description: str = Query(..., description="Job description to search resumes for")):
    if not job_description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    # Encode the input job description
    query_embedding = model.encode([job_description], convert_to_tensor=False)[0]

    # Connect to DB and fetch resumes
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, file_path, text, embedding FROM resumes WHERE processed = TRUE AND embedding IS NOT NULL")
    rows = cur.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No resumes found in the database.")

    # Calculate cosine similarity between query and each embedding
    similarities = []
    for resume_id, file_path, text, embedding in rows:
        if embedding:
            embedding = np.array(embedding)
            sim = np.dot(query_embedding, embedding) / (norm(query_embedding) * norm(embedding))
            similarities.append((sim, resume_id, file_path, text))

    # Sort by similarity (descending) and get top 5
    top_matches = sorted(similarities, key=lambda x: x[0], reverse=True)[:5]

    # Prepare results
    results = []
    for distance, resume_id, file_path, text in top_matches:
        filename = os.path.basename(file_path)
        results.append({
            "filename": filename,
            "text": text,
            "score": round((1 - distance) * 100, 2),  # simple similarity approximation
            "file_path": f"/pdfs/{filename}"
        })

    return {"query": job_description, "results": results[::-1]}  # reverse to show best at bottom


@app.get("/pdfs/{filename}")
async def get_pdf(filename: str):
    """Serve PDF files with proper path handling"""
    try:
        file_path = find_pdf(filename)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"PDF not found: {filename}")

        if not file_path.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Requested file is not a PDF")

        return FileResponse(
            file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PDF: {str(e)}")
