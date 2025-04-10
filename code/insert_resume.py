# code/insert_resumes.py

import os
from dbutils import get_db_connection

DATA_FOLDER = os.path.expanduser("~/Desktop/resume_screener_latest/data")

def insert_all_resumes():
    conn = get_db_connection()
    cur = conn.cursor()

    for root, dirs, files in os.walk(DATA_FOLDER):
        for file in files:
            if file.endswith(".pdf"):
                full_path = os.path.join(root, file)

                # Prevent duplicate insert
                cur.execute("SELECT COUNT(*) FROM resumes WHERE file_path = %s", (full_path,))
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                        INSERT INTO resumes (file_path, processed)
                        VALUES (%s, FALSE)
                    """, (full_path,))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ All new resumes inserted into database!")

if __name__ == "__main__":
    insert_all_resumes()
