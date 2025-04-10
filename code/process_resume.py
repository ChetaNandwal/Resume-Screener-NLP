# code/process_resumes.py

from dbutils import get_db_connection
from utility import extract_text, clean_text
from sentence_transformers import SentenceTransformer
import numpy as np
import ast

def fetch_unprocessed_resumes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, file_path FROM resumes WHERE processed = FALSE")
    resumes = cur.fetchall()
    cur.close()
    conn.close()
    return resumes

def update_resume_entry(resume_id, text, embedding):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE resumes
        SET text = %s,
            embedding = %s,
            processed = TRUE
        WHERE id = %s
    """, (text, embedding.tolist(), resume_id))
    conn.commit()
    cur.close()
    conn.close()

def process_resumes():
    print("🔍 Fetching unprocessed resumes from DB...")
    resumes = fetch_unprocessed_resumes()

    if not resumes:
        print("✅ All resumes already processed.")
        return

    print(f"📄 Found {len(resumes)} resumes to process.")

    # Load model once
    model = SentenceTransformer("all-MiniLM-L6-v2")

    for resume_id, file_path in resumes:
        print(f"📑 Processing: {file_path}")

        raw_text = extract_text(file_path)
        if not raw_text.strip():
            print(f"⚠️ No text extracted from {file_path}")
            continue

        cleaned = clean_text(raw_text)
        embedding = model.encode([cleaned])[0]

        update_resume_entry(resume_id, cleaned, embedding)
        print(f"✅ Updated resume ID {resume_id}")

    print("🎉 Done processing all resumes!")

if __name__ == "__main__":
    process_resumes()
