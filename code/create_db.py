from dbutils import get_db_connection

def create_resume_table():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS resumes(
                    id SERIAL PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    text TEXT,
                    embedding FLOAT8[],  -- PostgreSQL array for embeddings
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE
                );
                
                """)
    

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Table 'resumes' created successfully!")

if __name__ == "__main__":
    create_resume_table()