import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        dbname = "resume_db",
        user = "postgres",
        password = "chetan",
        host = "localhost",
        port = "5432"
    )
    return conn
