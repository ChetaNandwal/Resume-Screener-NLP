# main.py
import os
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
from config import *
from utility import *

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

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variables
df = None
faiss_index = None
embeddings = None
model = None

def initialize_system():
    """Run the full processing pipeline"""
    global df, faiss_index, embeddings, model
    
    print("🚀 Starting resume processing pipeline...")
    
    # Step 1: Extract text from PDFs
    if not os.path.exists(EXTRACTED_DATA):
        print("🔍 Extracting text from resumes...")
        resume_data = []
        
        for category in os.listdir(BASE_DIR):
            category_path = os.path.join(BASE_DIR, category)
            if os.path.isdir(category_path):
                for file in os.listdir(category_path):
                    if file.endswith(".pdf"):
                        pdf_path = os.path.join(category_path, file)
                        text = extract_text(pdf_path)
                        resume_data.append([file, category, text])
        
        df = pd.DataFrame(resume_data, columns=["Filename", "Category", "Extracted_Text"])
        df.to_csv(EXTRACTED_DATA, index=False)
        print(f"✅ Extracted {len(df)} resumes to {EXTRACTED_DATA}")
    else:
        df = pd.read_csv(EXTRACTED_DATA)
        print(f"📄 Using existing extracted data: {EXTRACTED_DATA}")

    # Step 2: Clean and process text
    if not os.path.exists(CLEANED_DATA):
        print("🧹 Cleaning resume text...")
        process_resumes(EXTRACTED_DATA, CLEANED_DATA)
    else:
        print(f"📄 Using existing cleaned data: {CLEANED_DATA}")
    
    df = pd.read_csv(CLEANED_DATA)

    # Step 3: Generate embeddings
    if not os.path.exists(EMBEDDINGS_PATH):
        print("🔢 Generating embeddings...")
        generate_embeddings(CLEANED_DATA, EMBEDDINGS_PATH)
    else:
        print(f"📄 Using existing embeddings: {EMBEDDINGS_PATH}")

    # Step 4: Build FAISS index
    if not os.path.exists(FAISS_INDEX_FILE):
        print("🏗️ Building FAISS index...")
        build_faiss_index(EMBEDDINGS_PATH, FAISS_INDEX_FILE)
    else:
        print(f"📄 Using existing FAISS index: {FAISS_INDEX_FILE}")

    # Load model and index
    print("⚙️ Loading model and index...")
    model = SentenceTransformer(MODEL_NAME)
    faiss_index, embeddings = load_faiss_index(FAISS_INDEX_FILE, EMBEDDINGS_PATH)
    
    print("🎉 System ready!")

# API Endpoints
# ... (keep all previous code until search endpoint)

@app.get("/search")
async def search(job_description: str = Query(..., description="Job description to search")):
    """Search resumes based on job description"""
    if not job_description:
        return {"error": "Job description cannot be empty"}
    
    # Convert query to embedding
    query_embedding = model.encode([job_description], convert_to_tensor=False)[0].astype("float32")
    
    # Search FAISS index
    distances, indices = faiss_index.search(np.array([query_embedding]), k=5)
    
    # Prepare results
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(df):
            results.append({
                "filename": df.iloc[idx]["Filename"],
                "category": df.iloc[idx]["Category"],
                "text": df.iloc[idx]["Cleaned_Text"],
                "score": abs((float(1 - distances[0][i]))*100),  # Convert to float for JSON
                "file_path": f"/pdfs/{df.iloc[idx]['Filename']}"
            })
    
    return {"query": job_description, "results": results}

@app.get("/pdfs/{filename}")
async def get_pdf(filename: str):
    """Serve PDF files"""
    file_path = find_pdf(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

# Initialize the system when starting
initialize_system()