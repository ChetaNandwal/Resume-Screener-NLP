# utils.py
import os
import fitz
import pandas as pd
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from fastapi.responses import FileResponse
from fastapi import HTTPException
from config import *

def extract_text(pdf_path):
    """Extract text from PDF file"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def clean_text(text):
    """Clean and normalize text"""
    
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special chars
    return text.strip()

def process_resumes(input_csv, output_csv):
    """Clean and process extracted resume text"""
    df = pd.read_csv(input_csv)
    
    if "Extracted_Text" not in df.columns:
        raise ValueError("Input CSV missing 'Extracted_Text' column")
    
    df["Extracted_Text"] = df["Extracted_Text"].fillna("")
    df["Cleaned_Text"] = df["Extracted_Text"].apply(clean_text)
    df = df[["Filename", "Category", "Cleaned_Text"]]
    df.to_csv(output_csv, index=False)
    print(f"✅ Processed {len(df)} resumes to {output_csv}")

def generate_embeddings(cleaned_csv, output_npy):
    """Generate embeddings from cleaned text"""
    df = pd.read_csv(cleaned_csv)
    
    if "Cleaned_Text" not in df.columns:
        raise ValueError("CSV missing 'Cleaned_Text' column")
    
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(df["Cleaned_Text"].tolist(), show_progress_bar=True)
    np.save(output_npy, embeddings)
    print(f"✅ Saved {len(embeddings)} embeddings to {output_npy}")

def build_faiss_index(embeddings_file, output_index_file):
    """Build FAISS index from embeddings"""
    embeddings = np.load(embeddings_file)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, output_index_file)
    print(f"✅ FAISS index saved to {output_index_file}")

def load_faiss_index(index_path, embeddings_path):
    """Load FAISS index and embeddings"""
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found: {index_path}")
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
    
    index = faiss.read_index(index_path)
    embeddings = np.load(embeddings_path)
    print("✅ FAISS index and embeddings loaded")
    return index, embeddings

def find_pdf(filename):
    """Locate PDF file in category folders"""
    for category in os.listdir(BASE_DIR):
        file_path = os.path.join(BASE_DIR, category, filename)
        if os.path.exists(file_path):
            return file_path
    return None