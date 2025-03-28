# config.py
import os

# Base directories
BASE_DIR = os.path.expanduser("~/Desktop/resume_screener_data/data")
PROJECT_DIR = os.path.expanduser("~/Desktop/resume_screener_deepseek")

# File paths
EXTRACTED_DATA = os.path.join(PROJECT_DIR, "extracted_resumes.csv")
CLEANED_DATA = os.path.join(PROJECT_DIR, "cleaned_data.csv")
EMBEDDINGS_PATH = os.path.join(PROJECT_DIR, "resume_embeddings.npy")
FAISS_INDEX_FILE = os.path.join(PROJECT_DIR, "faiss_index.bin")

# Model settings
MODEL_NAME = "all-MiniLM-L6-v2"