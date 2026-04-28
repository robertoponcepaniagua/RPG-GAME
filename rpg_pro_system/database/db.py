import psycopg2
import os

def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    return psycopg2.connect(database_url)

# PROBAR CONEXIÓN: docker compose exec app python database/db.py
if __name__ == "__main__":
    try:
        conn = get_connection()
        print("✅ Conexión exitosa a la base de datos")
        conn.close()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")